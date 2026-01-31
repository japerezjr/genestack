#!/bin/bash
# shellcheck disable=SC2034

# Gateway Utility Functions
# Common utility functions for gateway management

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "ERROR: kubectl is required but not installed"
        return 1
    fi
    return 0
}

# Function to check if a namespace exists
namespace_exists() {
    local namespace="$1"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get namespace "$namespace" &> /dev/null
    return $?
}

# Function to create a namespace
create_namespace() {
    local namespace="$1"
    
    if ! check_kubectl; then
        return 1
    fi
    
    if namespace_exists "$namespace"; then
        echo "Namespace '$namespace' already exists"
        return 0
    fi
    
    echo "Creating namespace: $namespace"
    kubectl create namespace "$namespace"
    return $?
}

# Function to check if a resource exists
resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    local namespace="${3:-default}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get "$resource_type" "$resource_name" -n "$namespace" &> /dev/null
    return $?
}

# Function to apply a Kubernetes manifest
apply_manifest() {
    local manifest_file="$1"
    local namespace="${2:-default}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    if [ ! -f "$manifest_file" ]; then
        echo "ERROR: Manifest file not found: $manifest_file"
        return 1
    fi
    
    echo "Applying manifest: $manifest_file"
    kubectl apply -f "$manifest_file" -n "$namespace"
    return $?
}

# Function to wait for a deployment to be ready
wait_for_deployment() {
    local deployment="$1"
    local namespace="${2:-default}"
    local timeout="${3:-300}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    echo "Waiting for deployment '$deployment' to be ready (timeout: ${timeout}s)"
    kubectl -n "$namespace" wait --timeout="${timeout}s" deployment "$deployment" --for=condition=available
    return $?
}

# Function to wait for a gateway to be programmed
wait_for_gateway() {
    local gateway="$1"
    local namespace="${2:-default}"
    local timeout="${3:-300}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    echo "Waiting for gateway '$gateway' to be programmed (timeout: ${timeout}s)"
    kubectl -n "$namespace" wait --timeout="${timeout}s" gateway "$gateway" --for=condition=Programmed
    return $?
}

# Function to get the external IP of a service
get_service_external_ip() {
    local service="$1"
    local namespace="${2:-default}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get service "$service" -n "$namespace" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null
}

# Function to get the external hostname of a service
get_service_external_hostname() {
    local service="$1"
    local namespace="${2:-default}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get service "$service" -n "$namespace" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null
}

# Function to label a node
label_node() {
    local node="$1"
    local label="$2"
    
    if ! check_kubectl; then
        return 1
    fi
    
    echo "Labeling node '$node' with '$label'"
    kubectl label node "$node" "$label" --overwrite
    return $?
}

# Function to check if a label exists on a node
node_has_label() {
    local node="$1"
    local label="$2"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get node "$node" -o jsonpath="{.metadata.labels.$label}" 2>/dev/null | grep -q .
    return $?
}

# Function to get all nodes with a specific label
get_nodes_with_label() {
    local label="$1"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get nodes -l "$label" -o jsonpath='{.items[*].metadata.name}'
}

# Function to create a secret from environment variables
create_secret_from_env() {
    local secret_name="$1"
    local namespace="$2"
    shift 2
    local env_vars=("$@")
    
    if ! check_kubectl; then
        return 1
    fi
    
    local secret_args=()
    for env_var in "${env_vars[@]}"; do
        local key="${env_var%%=*}"
        local value="${env_var#*=}"
        secret_args+=("--from-literal=$key=$value")
    done
    
    echo "Creating secret '$secret_name' in namespace '$namespace'"
    kubectl create secret generic "$secret_name" "${secret_args[@]}" -n "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    return $?
}

# Function to check if a secret exists
secret_exists() {
    local secret_name="$1"
    local namespace="${2:-default}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get secret "$secret_name" -n "$namespace" &> /dev/null
    return $?
}

# Function to get a secret value
get_secret_value() {
    local secret_name="$1"
    local key="$2"
    local namespace="${3:-default}"
    
    if ! check_kubectl; then
        return 1
    fi
    
    kubectl get secret "$secret_name" -n "$namespace" -o jsonpath="{.data.$key}" 2>/dev/null | base64 -d
}

# Function to print a formatted message
print_message() {
    local level="$1"
    local message="$2"
    
    case "$level" in
        INFO)
            echo "[INFO] $message"
            ;;
        WARN)
            echo "[WARN] $message" >&2
            ;;
        ERROR)
            echo "[ERROR] $message" >&2
            ;;
        SUCCESS)
            echo "[SUCCESS] $message"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Function to print a section header
print_section() {
    local title="$1"
    echo ""
    echo "=========================================="
    echo "$title"
    echo "=========================================="
    echo ""
}

# Function to check if a command exists
command_exists() {
    local command="$1"
    command -v "$command" &> /dev/null
    return $?
}

# Function to retry a command
retry_command() {
    local max_attempts="$1"
    local delay="$2"
    shift 2
    local command=("$@")
    
    local attempt=1
    while [ $attempt -le "$max_attempts" ]; do
        echo "Attempt $attempt/$max_attempts: ${command[*]}"
        
        if "${command[@]}"; then
            return 0
        fi
        
        if [ $attempt -lt "$max_attempts" ]; then
            echo "Command failed, retrying in ${delay}s..."
            sleep "$delay"
        fi
        
        ((attempt++))
    done
    
    echo "Command failed after $max_attempts attempts"
    return 1
}

# Function to validate required commands
validate_required_commands() {
    local commands=("$@")
    local missing_commands=()
    
    for cmd in "${commands[@]}"; do
        if ! command_exists "$cmd"; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        echo "ERROR: The following required commands are not installed:"
        for cmd in "${missing_commands[@]}"; do
            echo "  - $cmd"
        done
        return 1
    fi
    
    return 0
}
