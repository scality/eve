{{ define "eve.master" }}
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ template "fullname" $ }}-{{ .name }}
  labels:
    app: {{ template "fullname" $ }}
    chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
    release: "{{ .Release.Name }}"
    heritage: "{{ .Release.Service }}"
spec:
  serviceName: {{ template "fullname" $ }}-{{ .name }}
  replicas: 1
  selector:
    matchLabels:
      app: {{ template "fullname" $ }}-{{ .name }}
  template:
    metadata:
      labels:
        app: {{ template "fullname" $ }}-{{ .name }}
        chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
        release: "{{ .Release.Name }}"
    spec:
      {{- if .Values.image.pullSecrets }}
      imagePullSecrets:
        {{- range .Values.image.pullSecrets }}
        - name: {{ . }}
        {{- end }}
      {{- end }}
      containers:
      - name: master
        image: "{{ .Values.image.registry }}/{{ .Values.image.master.repository }}:{{ .Values.image.master.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy | quote }}
        ports:
        {{- if .isFrontend }}
        - containerPort: {{ .Values.deployment.ports.http }}
          name: http
          protocol: TCP
        {{- end }}
        {{- if .isMaster }}
        - containerPort: {{ .Values.deployment.ports.pb }}
          name: pb
          protocol: TCP
        {{- end }}
        livenessProbe:
          {{- if and .isMaster .hasCrossbar }}
          exec:
            command:
            - "lsof"
            - "-i"
            - "@{{ template "fullname" $ }}-crossbar.{{ $.Release.Namespace }}.svc.cluster.local"
{{ toYaml .Values.deployment.master.livenessProbe | indent 10 }}
          {{- else }}
          httpGet:
            path: /
            port: http
{{ toYaml .Values.deployment.frontend.livenessProbe | indent 10 }}
          {{- end }}
        resources:
        {{- if not .isMaster }}
{{ toYaml .Values.deployment.frontend.resources | indent 10 }}
        {{- else }}
{{ toYaml .Values.deployment.master.resources | indent 10 }}
        {{- end }}
        envFrom:
        - configMapRef:
            name: {{ template "fullname" $ }}-env
        - secretRef:
            name: {{ template "fullname" $ }}-env
        env:
        - name: MASTER_FQDN
          value: {{ printf .Values.eve.project.workerCallbackFqdn .index }}
        - name: MASTER_MODE
          value: {{ .mode }}
        {{- if .isMaster }}
        - name: SUFFIX
          value: {{ printf .Values.eve.project.resourceSuffix .index }}
        {{- else }}
        - name: SUFFIX
          value: {{ printf .Values.eve.project.resourceSuffix .index }}-frontend
        {{- end }}
        volumeMounts:
        - name: workspace
          mountPath: /root/eve/workers
        - name: files
          readOnly: true
          mountPath: /root/conf
        - name: files-secret
          readOnly: true
          mountPath: /root/conf-secret
        {{- if .Values.eve.masterConf.git.gitConfig }}
        - name: gitconfig
          readOnly: false
          mountPath: /etc/gitconfig
          subPath: gitconfig
        {{- end }}
        {{- if .isMaster }}
        - name: docker-host-data
          readOnly: false
          mountPath: /var/lib/docker
        - name: docker-host-sock
          readOnly: false
          mountPath: /var/run/docker.sock
        {{ end }}
        {{- if and .isMaster (eq .Values.eve.masterConf.dockerHook.dockerHookInUse "1") }}
        - name: docker-hook-binary
          readOnly: false
          mountPath: /usr/local/bin/docker
          subPath: docker
        {{- end }}
        {{- if .Values.registrySecret }}
        - name: docker-registry-credentials
          readOnly: true
          mountPath: /root/.docker/config.json
          subPath: .dockercfg
        {{- end }}
      - name: dind-daemon
        image: docker:dind
        resources:
          requests:
            cpu: 500m
            memory: 500Mi
        securityContext:
          privileged: true
        volumeMounts:
          - name: docker-storage
            mountPath: /var/lib/docker
      {{- if and .isMaster (eq .Values.eve.masterConf.dockerHook.dockerHookInUse "1") }}
      - name: docker-hook
        image: "{{ .Values.image.registry }}/{{ .Values.image.dockerHook.repository }}:{{ .Values.image.dockerHook.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy | quote }}
        securityContext:
          privileged: true
        livenessProbe:
          httpGet:
            path: /healthz
            port: 5000
{{ toYaml .Values.deployment.dockerHook.livenessProbe | indent 10 }}
        resources:
{{ toYaml .Values.deployment.dockerHook.resources | indent 10 }}
        lifecycle:
          preStop:
            exec:
              command:
              - "/bin/sh"
              - "-c"
              - >
                curl http://localhost:5000/quit
        env:
        - name: DOCKER_HOST
          value: localhost
        - name: DOCKER_API_VERSION
          value: {{ .Values.eve.masterConf.dockerWorkers.dockerApiVersion | quote }}
        - name: DOCKER_CONTAINER_MAX_MEMORY
          value: {{ .Values.eve.dockerHook.maxMemory | quote }}
        - name: NAMESPACE
          value: {{ $.Release.Namespace | quote }}
        - name: REGISTRY
          value: {{ .Values.eve.dockerHook.registry | quote }}
        - name: WORKER_DEADLINE
          value: {{ .Values.eve.dockerHook.activeDeadline | quote }}
        - name: WORKER_CPU_LIMIT
          value: {{ .Values.eve.dockerHook.cpuLimit | quote }}
        - name: WORKER_MEMORY_LIMIT
          value: {{ .Values.eve.dockerHook.memoryLimit | quote }}
        - name: WORKER_CPU_REQUEST
          value: {{ .Values.eve.dockerHook.cpuRequest | quote }}
        - name: WORKER_MEMORY_REQUEST
          value: {{ .Values.eve.dockerHook.memoryRequest | quote }}
        - name: VOLUME_LOCAL_BASEPATH
          value: {{ .Values.eve.dockerHook.volumeLocalBasePath | quote }}
        {{- range $key, $value := .Values.eve.dockerHook.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        command:
        - '/run.sh'
        volumeMounts:
        - name: docker-hook-credentials
          readOnly: true
          mountPath: /creds
        # - name: docker-host-data
        #   readOnly: false
        #   mountPath: /var/lib/docker
        # - name: docker-host-sock
        #   readOnly: false
        #   mountPath: /var/run/docker.sock
      {{ end }}
      volumes:
      - name: docker-storage
        emptyDir: {}
      - name: workspace
        emptyDir: {}
      - name: files
        configMap:
          name: {{ template "fullname" $ }}-files
      - name: files-secret
        secret:
          secretName: {{ template "fullname" $ }}-files
          defaultMode: 0600
      {{- if .Values.eve.masterConf.git.gitConfig }}
      - name: gitconfig
        configMap:
          name: {{ template "fullname" $ }}-gitconfig
      {{- end }}
      {{- if .isMaster }}
      - name: docker-host-data
        hostPath:
          path: /var/lib/docker
      - name: docker-host-sock
        hostPath:
          path: /var/run/docker.sock
      {{- end }}
      {{- if .Values.registrySecret }}
      - name: docker-registry-credentials
        secret:
          secretName: {{ .Values.registrySecret }}
      {{- end }}
      {{- if and .isMaster (eq .Values.eve.masterConf.dockerHook.dockerHookInUse "1") }}
      - name: docker-hook-binary
        configMap:
          name: {{ template "fullname" $ }}-docker-hook-binary
          defaultMode: 0755
      - name: docker-hook-credentials
        secret:
          secretName: {{ template "fullname" $ }}-docker-hook-credentials
      {{- end }}
      {{- if not .isMaster }}
      {{- with .Values.deployment.frontend.nodeSelector }}
      nodeSelector:
{{ toYaml . | indent 8 }}
      {{- end }}
      {{- with .Values.deployment.frontend.affinity }}
      affinity:
{{ toYaml . | indent 8 }}
      {{- end }}
      {{- with .Values.deployment.frontend.tolerations }}
      tolerations:
{{ toYaml . | indent 8 }}
      {{- end }}
      {{- else }}
      {{- with .Values.deployment.master.nodeSelector }}
      nodeSelector:
{{ toYaml . | indent 8 }}
      {{- end }}
      {{- with .Values.deployment.master.affinity }}
      affinity:
{{ toYaml . | indent 8 }}
      {{- end }}
      {{- with .Values.deployment.master.tolerations }}
      tolerations:
{{ toYaml . | indent 8 }}
      {{- end }}
      {{- end }}
{{- end }}
