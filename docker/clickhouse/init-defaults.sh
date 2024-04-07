#!/usr/bin/env sh

CLICKHOUSE_DB="${CLICKHOUSE_DB:-database}";
CLICKHOUSE_USER="${CLICKHOUSE_USER:-user}";
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-password}";

cat <<EOT >> /etc/clickhouse-server/users.d/user.xml
<yandex>
  <!-- Docs: <https://clickhouse.tech/docs/en/operations/settings/settings_users/> -->
  <users>
    <${CLICKHOUSE_USER}>
      <profile>default</profile>
      <networks>
        <ip>::/0</ip>
      </networks>
      <password>${CLICKHOUSE_PASSWORD}</password>
      <quota>default</quota>
    </${CLICKHOUSE_USER}>
  </users>
</yandex>
EOT
#cat /etc/clickhouse-server/users.d/user.xml;

clickhouse-client --query "CREATE DATABASE IF NOT EXISTS ${CLICKHOUSE_DB}";