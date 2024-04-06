package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	s3 "github.com/fclairamb/afero-s3"
	"github.com/google/uuid"
	"github.com/kelseyhightower/envconfig"
	"github.com/pkg/errors"
	"github.com/spf13/afero"
)

type config struct {
	BaseURL        string `envconfig:"IMGPROXY_PUBLIC_URL"`
	SigningKeyHex  string `envconfig:"IMGPROXY_SIGNING_KEY"`
	SigningSaltHex string `envconfig:"IMGPROXY_SIGNING_SALT"`
}

type imageHandler struct {
	baseURL     string
	signingKey  []byte
	signingSalt []byte
	storage     afero.Fs
}

func newimageHandler(cfg config, storage afero.Fs) (*imageHandler, error) {
	// Prepare the url signing key and salt
	key, err := hex.DecodeString(cfg.SigningKeyHex)
	if err != nil {
		return nil, errors.Wrap(err, "Key expected to be hex-encoded string")
	}

	salt, err := hex.DecodeString(cfg.SigningSaltHex)
	if err != nil {
		return nil, errors.Wrap(err, "Salt expected to be hex-encoded string")
	}

	img := &imageHandler{
		baseURL:     cfg.BaseURL,
		signingKey:  key,
		signingSalt: salt,
		storage:     storage,
	}

	return img, nil
}

func (ih *imageHandler) store(key string, image io.Reader) error {
	file, err := ih.storage.OpenFile(key, os.O_WRONLY, 0777)
	if err != nil {
		return errors.Wrap(err, "failed to open image")
	}

	defer file.Close()

	_, err = io.Copy(file, image)
	if err != nil {
		return errors.Wrap(err, "failed to store image")
	}

	return file.Close()
}

func (ih *imageHandler) sign(path string) string {
	mac := hmac.New(sha256.New, ih.signingKey)
	mac.Write(ih.signingSalt) // FIXME: possible error?
	mac.Write([]byte(path))   // FIXME: possible error?

	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

func (ih *imageHandler) generateURL(imgURI string) string {
	// TODO: The properties are set here for simplicity.
	// but will be an argument to the function in a real application
	// resize := "fill"
	// width := 300
	// height := 300
	// gravity := "no"
	// enlarge := 1
	extension := "png"

	imgURI = base64.RawURLEncoding.EncodeToString([]byte(imgURI))
	// path := fmt.Sprintf("/rs:%s:%d:%d:%d/g:%s/%s.%s", resize, width, height, enlarge, gravity, imgURI, extension)
	//plain resizing arguments
	// path := fmt.Sprintf("/%s.%s", imgURI, extension)
	path := fmt.Sprintf("/dpr:0.3333/%s.%s", imgURI, extension)

	return fmt.Sprintf("%s/%s%s", ih.baseURL, ih.sign(path), path)
}

func (ih *imageHandler) handler(bucket string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Maximum upload of 100 MB files
		err := r.ParseMultipartForm(100 << 20)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		// Get the file from the request
		// Note that the argument to FormFile should match the name attribute
		// of the upload input tag in the form.
		file, handler, err := r.FormFile("image")
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		defer file.Close()

		// Generate a unique key for the image
		// We'll be using a uuid for this example
		// but any unique string goes
		//
		// FYI this is not a 100% reliable way to determine file type
		// but it's good enough for this example
		imgKey := uuid.NewString() + path.Ext(handler.Filename)

		// Store the image
		err = ih.store(imgKey, file)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		// TODO: save the image key in the database as needed.

		// Generate the URL for the image
		imgURL := ih.generateURL(fmt.Sprintf("s3://%s/%s", bucket, imgKey))

		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "Image URL: %s", imgURL)
	}
}

func main() {
	var cfg struct {
		// Extra configuration for setting up connection to the file storage
		AccessKey    string `envconfig:"ACCESS_KEY"`
		AccessSecret string `envconfig:"ACCESS_SECRET"`
		Bucket       string `envconfig:"IMG_UPLOAD_BUCKET"`
		Endpoint     string `envconfig:"RESOURCE_ENDPOINT"`
		Region       string `envconfig:"RESOURCE_REGION"`

		ImgConfig config
	}

	err := envconfig.Process("", &cfg)
	if err != nil {
		panic(err)
	}

	// Create a file system for storing the images
	sess, err := session.NewSession(&aws.Config{
		Region:           aws.String(cfg.Region),
		Endpoint:         aws.String(cfg.Endpoint),
		Credentials:      credentials.NewStaticCredentials(cfg.AccessKey, cfg.AccessSecret, ""),
		S3ForcePathStyle: aws.Bool(true),
	})
	if err != nil {
		panic(err)
	}

	img, err := newimageHandler(cfg.ImgConfig, s3.NewFs(cfg.Bucket, sess))
	if err != nil {
		panic(err)
	}

	mux := http.NewServeMux()
	mux.Handle("/", img.handler(cfg.Bucket))

	fmt.Println("Starting server on port", ":8080")
	http.ListenAndServe(":8080", mux)
}
