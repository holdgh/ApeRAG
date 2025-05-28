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
  {{- $ctx.Values.postgres.POSTGRES_HOST -}}
{{- end }}

# POSTGRES_PORT
{{- define "database.postgresPort" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.postgres.POSTGRES_PORT -}}
{{- end }}

# POSTGRES_DB
{{- define "database.postgresDB" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.postgres.POSTGRES_DB -}}
{{- end }}

# POSTGRES_USER
{{- define "database.postgresUser" -}}
  {{- $ctx := . -}}
  {{- $credSecret := dict }}
  {{- if $ctx.Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME }}
    {{- $credSecret = lookup "v1" "Secret" $ctx.Release.Namespace $ctx.Values.postgres.POSTGRES_CREDENTIALS_SECRET_NAME }}
  {{- end }}

  {{- if and $credSecret (hasKey $credSecret.data "username") }}
    {{- $credSecret.data.username | b64dec }}
  {{- else }}
    {{- $ctx.Values.postgres.POSTGRES_USER -}}
  {{- end }}
{{- end }}

# POSTGRES_PASSWORD
{{- define "database.postgresPassword" -}}
  {{- $ctx := . -}}
  {{- if $ctx.Values.postgres.POSTGRES_PASSWORD }}
    {{- $ctx.Values.postgres.POSTGRES_PASSWORD }}
  {{- else }}
    {{- "postgres" }}
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
  {{- $ctx.Values.redis.REDIS_HOST -}}
{{- end }}

# REDIS_PORT
{{- define "database.redisPort" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.redis.REDIS_PORT -}}
{{- end }}

# REDIS_USER
{{- define "database.redisUser" -}}
  {{- $ctx := . -}}
  {{- if $ctx.Values.redis.REDIS_USER }}
    {{- $ctx.Values.redis.REDIS_USER }}
  {{- else }}
    {{- "default" }}
  {{- end }}
{{- end }}

# REDIS_PASSWORD
{{- define "database.redisPassword" -}}
  {{- $ctx := . -}}
  {{- if $ctx.Values.redis.REDIS_PASSWORD }}
    {{- $ctx.Values.redis.REDIS_PASSWORD }}
  {{- else }}
    {{- "redis" }}
  {{- end }}
{{- end }}

# CELERY_BROKER_URL Helper (builds URL from Redis helpers)
{{- define "database.celeryBrokerUrl" -}}
  {{- $ctx := . -}}
  {{- $host := include "database.redisHost" $ctx -}}
  {{- $port := include "database.redisPort" $ctx -}}
  {{- $user := include "database.redisUser" $ctx -}}
  {{- $password := include "database.redisPassword" $ctx -}}

  {{- printf "redis://%s:%s@%s:%s/0" $user $password $host $port -}}
{{- end }}

# MEMORY_REDIS_URL Helper (builds URL from Redis helpers, typically without DB number for generic cache)
{{- define "database.memoryRedisUrl" -}}
  {{- $ctx := . -}}
  {{- $host := include "database.redisHost" $ctx -}}
  {{- $port := include "database.redisPort" $ctx -}}
  {{- $user := include "database.redisUser" $ctx -}}
  {{- $password := include "database.redisPassword" $ctx -}}

  {{- printf "redis://%s:%s@%s:%s/1" $user $password $host $port -}}
{{- end }}


# ES_HOST
{{- define "database.esHost" -}}
  {{- $ctx := . -}}
  {{- $protocol := $ctx.Values.elasticsearch.ES_PROTOCOL | default "http" -}}
  {{- $host := $ctx.Values.elasticsearch.ES_HOST -}}
  {{- $port := $ctx.Values.elasticsearch.ES_PORT -}}

  {{- $user := include "database.esUser" $ctx -}}
  {{- $password := include "database.esPassword" $ctx -}}

  {{- if $user }}
    {{- printf "%s://%s:%s@%s:%s" $protocol $user $password $host $port -}}
  {{- else }}
    {{- printf "%s://%s:%s" $protocol $host $port -}}
  {{- end }}
{{- end }}

# ES_PROTOCOL (if you want to control it separately)
{{- define "database.esProtocol" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.elasticsearch.ES_PROTOCOL | default "http" -}}
{{- end }}

# ES_PORT (if you want to control it separately)
{{- define "database.esPort" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.elasticsearch.ES_PORT | default "9200" -}}
{{- end }}

# ES_USER
{{- define "database.esUser" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.elasticsearch.ES_USER -}}
{{- end }}

# ES_PASSWORD
{{- define "database.esPassword" -}}
  {{- $ctx := . -}}
  {{- $ctx.Values.elasticsearch.ES_PASSWORD -}}
{{- end }}