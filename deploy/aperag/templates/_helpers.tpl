{{/*
Expand the name of the chart.
*/}}
{{- define "aperag.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "aperag.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "aperag.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "aperag.labels" -}}
helm.sh/chart: {{ include "aperag.chart" . }}
{{ include "aperag.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "aperag.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aperag.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "aperag.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "aperag.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{- define "django.labels" -}}
app.aperag.io/component: django
{{- end }}

{{- define "celeryworker.labels" -}}
app.aperag.io/component: celery-worker
{{- end }}

{{- define "frontend.labels" -}}
app.aperag.io/component: frontend
{{- end }}

# POSTGRES_HOST
{{- define "database.postgresHost" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.postgres.POSTGRES_HOST -}} # Returns value from values.yaml
{{- end }}

# POSTGRES_PORT
{{- define "database.postgresPort" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.postgres.POSTGRES_PORT -}} # Returns value from values.yaml
{{- end }}

# POSTGRES_DB
{{- define "database.postgresDB" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.postgres.POSTGRES_DB -}} # Returns value from values.yaml
{{- end }}

# POSTGRES_USER
{{- define "database.postgresUser" -}}
  {{- $ctx := . -}}
  {{- $credSecret := dict }}
  {{- if $ctx.Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME }} # Use unified secret name
    {{- $credSecret = lookup "v1" "Secret" $ctx.Release.Namespace $ctx.Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME }}
  {{- end }}

  {{- if and $credSecret (hasKey $credSecret.data "username") }} # Check 'username' key in the unified secret
    {{- $credSecret.data.username | b64dec }}
  {{- else }}
    {{- $ctx.Values.postgres.POSTGRES_USER -}} # Returns value from values.yaml (could be the default "postgres")
  {{- end }}
{{- end }}

# POSTGRES_PASSWORD
{{- define "database.postgresPassword" -}}
  {{- $ctx := . -}}
  {{- $credSecret := dict }}
  {{- if $ctx.Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME }} # Use unified secret name
    {{- $credSecret = lookup "v1" "Secret" $ctx.Release.Namespace $ctx.Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME }}
  {{- end }}

  {{- if and $credSecret (hasKey $credSecret.data "password") }} # Check 'password' key in the unified secret
    {{- $credSecret.data.password | b64dec }}
  {{- else if $ctx.Values.postgres.POSTGRES_PASSWORD }}
    {{- $ctx.Values.postgres.POSTGRES_PASSWORD }}
  {{- else }}
    {{- required "POSTGRES_PASSWORD not found. Please set .Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME or provide .Values.postgres.POSTGRES_PASSWORD directly in values.yaml (not recommended for production)." nil }}
  {{- end }}
{{- end }}

# DATABASE_URL Helper (Unchanged, builds URL from other helpers)
{{- define "database.databaseUrl" -}}
  {{- $ctx := . -}}
  {{- $host := include "database.postgresHost" $ctx -}}
  {{- $port := include "database.postgresPort" $ctx -}}
  {{- $db := include "database.postgresDB" $ctx -}}
  {{- $user := include "database.postgresUser" $ctx -}}
  {{- $password := include "database.postgresPassword" $ctx -}}

  {{- printf "postgresql://%s:%s@%s:%s/%s" $user $password $host $port $db -}}
{{- end }}



# REDIS_HOST
{{- define "database.redisHost" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.redis.REDIS_HOST -}} # Returns value from values.yaml
{{- end }}

# REDIS_PORT
{{- define "database.redisPort" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.redis.REDIS_PORT -}} # Returns value from values.yaml
{{- end }}

# REDIS_USER
{{- define "database.redisUser" -}}
  {{- $ctx := . -}}
  {{- $credSecret := dict }}
  {{- if $ctx.Values.redis.REDIS_CREDENTIALS_SECRET_NAME }}
    {{- $credSecret = lookup "v1" "Secret" $ctx.Release.Namespace $ctx.Values.redis.REDIS_CREDENTIALS_SECRET_NAME }}
  {{- end }}

  {{- if and $credSecret (hasKey $credSecret.data "username") }} # Assuming Redis secret has 'username' key
    {{- $credSecret.data.username | b64dec }}
  {{- else }}
    {{- $ctx.Values.redis.REDIS_USER -}} # Returns value from values.yaml (could be the default "default")
  {{- end }}
{{- end }}

# REDIS_PASSWORD
{{- define "database.redisPassword" -}}
  {{- $ctx := . -}}
  {{- $credSecret := dict }}
  {{- if $ctx.Values.redis.REDIS_CREDENTIALS_SECRET_NAME }}
    {{- $credSecret = lookup "v1" "Secret" $ctx.Release.Namespace $ctx.Values.redis.REDIS_CREDENTIALS_SECRET_NAME }}
  {{- end }}

  {{- if and $credSecret (hasKey $credSecret.data "password") }} # Assuming Redis secret has 'password' key
    {{- $credSecret.data.password | b64dec }}
  {{- else if $ctx.Values.redis.REDIS_PASSWORD }}
    {{- $ctx.Values.redis.REDIS_PASSWORD }}
  {{- else }}
    {{- required "REDIS_PASSWORD not found. Please set .Values.redis.REDIS_CREDENTIALS_SECRET_NAME or provide .Values.redis.REDIS_PASSWORD directly in values.yaml (not recommended for production)." nil }}
  {{- end }}
{{- end }}

# CELERY_BROKER_URL Helper (builds URL from Redis helpers)
{{- define "database.celeryBrokerUrl" -}}
  {{- $ctx := . -}}
  {{- $host := include "database.redisHost" $ctx -}}
  {{- $port := include "database.redisPort" $ctx -}}
  {{- $user := include "database.redisUser" $ctx -}}
  {{- $password := include "database.redisPassword" $ctx -}}

  {{- printf "redis://%s:%s@%s:%s/0" $user $password $host $port -}} # Assuming database 0
{{- end }}

# MEMORY_REDIS_URL Helper (builds URL from Redis helpers, typically without DB number for generic cache)
{{- define "database.memoryRedisUrl" -}}
  {{- $ctx := . -}}
  {{- $host := include "database.redisHost" $ctx -}}
  {{- $port := include "database.redisPort" $ctx -}}
  {{- $user := include "database.redisUser" $ctx -}}
  {{- $password := include "database.redisPassword" $ctx -}}

  {{- printf "redis://%s:%s@%s:%s/1" $user $password $host $port -}} # Assuming database 0
{{- end }}