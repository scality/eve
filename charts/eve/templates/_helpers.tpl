{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "fullname" -}}
{{- if .Values.useShortNames }}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Print elements in masterConf except secrets and files.

We know a value is a secret if its name is declared in
secrets.txt. Likewise, files are declared in _files.txt.
*/}}
{{- define "printConf" -}}
{{- $secrets := .Files.Lines "_secrets.txt" }}
{{- $files := .Files.Lines "_files.txt" }}
{{- range $section, $data := .Values.eve.masterConf }}
{{- range $key, $value := $data }}
{{- $path := printf "eve.masterConf.%s.%s" $section $key }}
{{- if and (not (has $path $secrets)) (not (has $path $files)) }}
  {{ snakecase $key | upper }}: {{ $value | quote }}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Print secrets found in masterConf
*/}}
{{- define "printSecrets" -}}
{{- $secrets := (.Files.Lines "_secrets.txt") }}
{{- range $section, $data := .Values.eve.masterConf }}
{{- range $key, $value := $data }}
{{- $path := printf "eve.masterConf.%s.%s" $section $key }}
{{- if has $path $secrets }}
  {{ snakecase $key | upper }}: {{ $value | b64enc | quote }}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}
