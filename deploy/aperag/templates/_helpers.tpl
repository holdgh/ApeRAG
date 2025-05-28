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

# DATABASE_URL Helper - builds complete PostgreSQL URL
{{- define "database.databaseUrl" -}}
  {{- $ctx := . -}}
  {{- $host := $ctx.Values.postgres.POSTGRES_HOST -}}
  {{- $port := $ctx.Values.postgres.POSTGRES_PORT -}}
  {{- $db := $ctx.Values.postgres.POSTGRES_DB -}}
  {{- $user := $ctx.Values.postgres.POSTGRES_USER | default "postgres" -}}
  {{- $password := $ctx.Values.postgres.POSTGRES_PASSWORD | default "postgres" -}}

  {{- printf "postgresql://%s:%s@%s:%s/%s" $user $password $host $port $db -}}
{{- end }}

# CELERY_BROKER_URL Helper - builds Redis URL for Celery
{{- define "database.celeryBrokerUrl" -}}
  {{- $ctx := . -}}
  {{- $host := $ctx.Values.redis.REDIS_HOST -}}
  {{- $port := $ctx.Values.redis.REDIS_PORT -}}
  {{- $user := $ctx.Values.redis.REDIS_USER | default "default" -}}
  {{- $password := $ctx.Values.redis.REDIS_PASSWORD | default "redis" -}}

  {{- printf "redis://%s:%s@%s:%s/0" $user $password $host $port -}}
{{- end }}

# MEMORY_REDIS_URL Helper - builds Redis URL for memory cache
{{- define "database.memoryRedisUrl" -}}
  {{- $ctx := . -}}
  {{- $host := $ctx.Values.redis.REDIS_HOST -}}
  {{- $port := $ctx.Values.redis.REDIS_PORT -}}
  {{- $user := $ctx.Values.redis.REDIS_USER | default "default" -}}
  {{- $password := $ctx.Values.redis.REDIS_PASSWORD | default "redis" -}}

  {{- printf "redis://%s:%s@%s:%s/1" $user $password $host $port -}}
{{- end }}

# ES_HOST - builds complete Elasticsearch URL with authentication
{{- define "database.esHost" -}}
  {{- $ctx := . -}}
  {{- $protocol := $ctx.Values.elasticsearch.ES_PROTOCOL | default "http" -}}
  {{- $host := $ctx.Values.elasticsearch.ES_HOST -}}
  {{- $port := $ctx.Values.elasticsearch.ES_PORT -}}
  {{- $user := $ctx.Values.elasticsearch.ES_USER -}}
  {{- $password := $ctx.Values.elasticsearch.ES_PASSWORD -}}

  {{- if $user }}
    {{- printf "%s://%s:%s@%s:%s" $protocol $user $password $host $port -}}
  {{- else }}
    {{- printf "%s://%s:%s" $protocol $host $port -}}
  {{- end }}
{{- end }}