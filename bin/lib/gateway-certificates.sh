#!/bin/bash
# shellcheck disable=SC2034,SC2155

# Gateway Certificate Management
# Handles certificate provisioning, validation, and DNS provider integration

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-config.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-utils.sh"

# Function to validate DNS provider credentials
validate_dns_credentials() {
    local dns_provider="$1"
    local gateway_name="$2"
    
    case "$dns_provider" in
        cloudflare)
            local api_token
            api_token=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_token")
            if [ -z "$api_token" ]; then
                print_message "ERROR" "Cloudflare API token is required"
                return 1
            fi
            ;;
        route53)
            local access_key_id
            local secret_access_key
            access_key_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.access_key_id")
            secret_access_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.secret_access_key")
            if [ -z "$access_key_id" ] || [ -z "$secret_access_key" ]; then
                print_message "ERROR" "AWS Route53 credentials (access_key_id and secret_access_key) are required"
                return 1
            fi
            ;;
        azuredns)
            local subscription_id
            local tenant_id
            local client_id
            local client_secret
            subscription_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.subscription_id")
            tenant_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tenant_id")
            client_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.client_id")
            client_secret=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.client_secret")
            if [ -z "$subscription_id" ] || [ -z "$tenant_id" ] || [ -z "$client_id" ] || [ -z "$client_secret" ]; then
                print_message "ERROR" "Azure DNS credentials (subscription_id, tenant_id, client_id, client_secret) are required"
                return 1
            fi
            ;;
        google)
            local service_account_key
            service_account_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.service_account_key")
            if [ -z "$service_account_key" ]; then
                print_message "ERROR" "Google Cloud DNS service account key is required"
                return 1
            fi
            ;;
        digitalocean)
            local api_token
            api_token=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_token")
            if [ -z "$api_token" ]; then
                print_message "ERROR" "DigitalOcean API token is required"
                return 1
            fi
            ;;
        godaddy)
            local api_key
            local api_secret
            api_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_key")
            api_secret=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_secret")
            if [ -z "$api_key" ] || [ -z "$api_secret" ]; then
                print_message "ERROR" "GoDaddy API credentials (api_key and api_secret) are required"
                return 1
            fi
            ;;
        rackspace)
            local username
            local api_key
            username=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.username")
            api_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_key")
            if [ -z "$username" ] || [ -z "$api_key" ]; then
                print_message "ERROR" "Rackspace credentials (username and api_key) are required"
                return 1
            fi
            ;;
        acmedns)
            local host
            local api_key
            host=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.host")
            api_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_key")
            if [ -z "$host" ] || [ -z "$api_key" ]; then
                print_message "ERROR" "ACME-DNS credentials (host and api_key) are required"
                return 1
            fi
            ;;
        rfc2136)
            local nameserver
            local tsig_key_name
            local tsig_secret
            nameserver=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.nameserver")
            tsig_key_name=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tsig_key_name")
            tsig_secret=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tsig_secret")
            if [ -z "$nameserver" ] || [ -z "$tsig_key_name" ] || [ -z "$tsig_secret" ]; then
                print_message "ERROR" "RFC2136 credentials (nameserver, tsig_key_name, tsig_secret) are required"
                return 1
            fi
            ;;
        *)
            print_message "ERROR" "Unsupported DNS provider: $dns_provider"
            return 1
            ;;
    esac
    
    return 0
}

# Function to create DNS credentials secret
create_dns_credentials_secret() {
    local gateway_name="$1"
    local namespace="$2"
    local dns_provider="$3"
    
    local secret_name="${gateway_name}-dns-credentials"
    
    print_message "INFO" "Creating DNS credentials secret: $secret_name"
    
    case "$dns_provider" in
        cloudflare)
            local api_token
            api_token=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_token")
            kubectl create secret generic "$secret_name" \
                --from-literal=api-token="$api_token" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        route53)
            local access_key_id
            local secret_access_key
            local hosted_zone_id
            access_key_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.access_key_id")
            secret_access_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.secret_access_key")
            hosted_zone_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.hosted_zone_id" "")
            
            if [ -n "$hosted_zone_id" ]; then
                kubectl create secret generic "$secret_name" \
                    --from-literal=access-key-id="$access_key_id" \
                    --from-literal=secret-access-key="$secret_access_key" \
                    --from-literal=hosted-zone-id="$hosted_zone_id" \
                    -n "$namespace" \
                    --dry-run=client -o yaml | kubectl apply -f -
            else
                kubectl create secret generic "$secret_name" \
                    --from-literal=access-key-id="$access_key_id" \
                    --from-literal=secret-access-key="$secret_access_key" \
                    -n "$namespace" \
                    --dry-run=client -o yaml | kubectl apply -f -
            fi
            ;;
        azuredns)
            local subscription_id
            local tenant_id
            local client_id
            local client_secret
            local resource_group
            subscription_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.subscription_id")
            tenant_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tenant_id")
            client_id=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.client_id")
            client_secret=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.client_secret")
            resource_group=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.resource_group" "")
            
            kubectl create secret generic "$secret_name" \
                --from-literal=subscription-id="$subscription_id" \
                --from-literal=tenant-id="$tenant_id" \
                --from-literal=client-id="$client_id" \
                --from-literal=client-secret="$client_secret" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        google)
            local service_account_key
            service_account_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.service_account_key")
            
            # Create temporary file for service account key
            local temp_file
            temp_file=$(mktemp)
            echo "$service_account_key" > "$temp_file"
            
            kubectl create secret generic "$secret_name" \
                --from-file=service-account.json="$temp_file" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            
            rm -f "$temp_file"
            ;;
        digitalocean)
            local api_token
            api_token=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_token")
            kubectl create secret generic "$secret_name" \
                --from-literal=api-token="$api_token" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        godaddy)
            local api_key
            local api_secret
            api_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_key")
            api_secret=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_secret")
            kubectl create secret generic "$secret_name" \
                --from-literal=api-key="$api_key" \
                --from-literal=api-secret="$api_secret" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        rackspace)
            local username
            local api_key
            username=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.username")
            api_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_key")
            kubectl create secret generic "$secret_name" \
                --from-literal=username="$username" \
                --from-literal=api-key="$api_key" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        acmedns)
            local host
            local api_key
            host=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.host")
            api_key=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.api_key")
            kubectl create secret generic "$secret_name" \
                --from-literal=host="$host" \
                --from-literal=api-key="$api_key" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        rfc2136)
            local nameserver
            local tsig_key_name
            local tsig_secret
            local tsig_algorithm
            nameserver=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.nameserver")
            tsig_key_name=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tsig_key_name")
            tsig_secret=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tsig_secret")
            tsig_algorithm=$(get_config_value "gateways.$gateway_name.certificate.dns_credentials.tsig_algorithm" "HMACSHA256")
            kubectl create secret generic "$secret_name" \
                --from-literal=nameserver="$nameserver" \
                --from-literal=tsig-key-name="$tsig_key_name" \
                --from-literal=tsig-secret="$tsig_secret" \
                --from-literal=tsig-algorithm="$tsig_algorithm" \
                -n "$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            ;;
        *)
            print_message "ERROR" "Unsupported DNS provider: $dns_provider"
            return 1
            ;;
    esac
    
    return $?
}

# Function to setup certificate provider
setup_certificate_provider() {
    local gateway_name="$1"
    local namespace="$2"
    
    local cert_provider
    local email
    local acme_challenge
    local dns_provider
    
    cert_provider=$(get_config_value "gateways.$gateway_name.certificate.provider" "self-signed")
    email=$(get_config_value "gateways.$gateway_name.certificate.email" "")
    acme_challenge=$(get_config_value "gateways.$gateway_name.certificate.acme_challenge" "http01")
    dns_provider=$(get_config_value "gateways.$gateway_name.certificate.dns_provider" "")
    
    print_message "INFO" "Setting up certificate provider: $cert_provider"
    
    case "$cert_provider" in
        letsencrypt)
            if [ -z "$email" ]; then
                print_message "ERROR" "Email is required for Let's Encrypt"
                return 1
            fi
            
            # Validate and create DNS credentials if using DNS01
            if [ "$acme_challenge" = "dns01" ]; then
                if [ -z "$dns_provider" ]; then
                    print_message "ERROR" "DNS provider is required for DNS01 challenge"
                    return 1
                fi
                
                if ! validate_dns_credentials "$dns_provider" "$gateway_name"; then
                    return 1
                fi
                
                if ! create_dns_credentials_secret "$gateway_name" "$namespace" "$dns_provider"; then
                    print_message "ERROR" "Failed to create DNS credentials secret"
                    return 1
                fi
            fi
            
            print_message "SUCCESS" "Certificate provider setup complete"
            ;;
        self-signed)
            print_message "INFO" "Using self-signed certificates"
            ;;
        custom)
            print_message "INFO" "Using custom certificate management"
            ;;
        *)
            print_message "ERROR" "Unsupported certificate provider: $cert_provider"
            return 1
            ;;
    esac
    
    return 0
}

# Function to check certificate status
check_certificate_status() {
    local cert_name="$1"
    local namespace="$2"
    
    if ! kubectl get certificate "$cert_name" -n "$namespace" &>/dev/null; then
        print_message "WARN" "Certificate $cert_name not found"
        return 1
    fi
    
    local ready
    ready=$(kubectl get certificate "$cert_name" -n "$namespace" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
    
    if [ "$ready" = "True" ]; then
        print_message "SUCCESS" "Certificate $cert_name is ready"
        return 0
    else
        print_message "WARN" "Certificate $cert_name is not ready"
        local reason
        reason=$(kubectl get certificate "$cert_name" -n "$namespace" -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}' 2>/dev/null)
        if [ -n "$reason" ]; then
            print_message "INFO" "Reason: $reason"
        fi
        return 1
    fi
}

# Function to wait for certificate to be ready
wait_for_certificate() {
    local cert_name="$1"
    local namespace="$2"
    local timeout="${3:-300}"
    
    print_message "INFO" "Waiting for certificate $cert_name to be ready (timeout: ${timeout}s)"
    
    local elapsed=0
    local interval=10
    
    while [ $elapsed -lt $timeout ]; do
        if check_certificate_status "$cert_name" "$namespace"; then
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        print_message "INFO" "Still waiting... (${elapsed}s/${timeout}s)"
    done
    
    print_message "ERROR" "Certificate did not become ready within timeout"
    return 1
}

# Function to renew certificate
renew_certificate() {
    local cert_name="$1"
    local namespace="$2"
    
    print_message "INFO" "Triggering certificate renewal: $cert_name"
    
    # Delete and recreate the certificate to trigger renewal
    kubectl delete certificate "$cert_name" -n "$namespace" --ignore-not-found=true
    
    # The certificate will be recreated by the gateway setup
    print_message "INFO" "Certificate renewal triggered"
    
    return 0
}

# Function to get certificate expiry
get_certificate_expiry() {
    local cert_name="$1"
    local namespace="$2"
    
    local secret_name="${cert_name}-tls"
    
    if ! kubectl get secret "$secret_name" -n "$namespace" &>/dev/null; then
        print_message "WARN" "Certificate secret $secret_name not found"
        return 1
    fi
    
    local cert_data
    cert_data=$(kubectl get secret "$secret_name" -n "$namespace" -o jsonpath='{.data.tls\.crt}' 2>/dev/null | base64 -d)
    
    if [ -z "$cert_data" ]; then
        print_message "WARN" "Certificate data not found in secret"
        return 1
    fi
    
    # Extract expiry date using openssl
    local expiry
    expiry=$(echo "$cert_data" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    
    if [ -n "$expiry" ]; then
        print_message "INFO" "Certificate expires: $expiry"
        return 0
    else
        print_message "WARN" "Could not determine certificate expiry"
        return 1
    fi
}

# Function to list all certificates for a gateway
list_gateway_certificates() {
    local gateway_name="$1"
    local namespace="$2"
    
    print_message "INFO" "Certificates for gateway $gateway_name:"
    kubectl get certificate -n "$namespace" -l "gateway.envoyproxy.io/owning-gateway-name=$gateway_name" 2>/dev/null
    
    return $?
}

# Function to validate certificate configuration
validate_certificate_config() {
    local gateway_name="$1"
    
    local cert_provider
    local email
    local acme_challenge
    local dns_provider
    
    cert_provider=$(get_config_value "gateways.$gateway_name.certificate.provider" "self-signed")
    email=$(get_config_value "gateways.$gateway_name.certificate.email" "")
    acme_challenge=$(get_config_value "gateways.$gateway_name.certificate.acme_challenge" "http01")
    dns_provider=$(get_config_value "gateways.$gateway_name.certificate.dns_provider" "")
    
    print_message "INFO" "Validating certificate configuration for gateway: $gateway_name"
    
    case "$cert_provider" in
        letsencrypt)
            if [ -z "$email" ]; then
                print_message "ERROR" "Email is required for Let's Encrypt"
                return 1
            fi
            
            if [ "$acme_challenge" = "dns01" ]; then
                if [ -z "$dns_provider" ]; then
                    print_message "ERROR" "DNS provider is required for DNS01 challenge"
                    return 1
                fi
                
                if ! validate_dns_credentials "$dns_provider" "$gateway_name"; then
                    return 1
                fi
            fi
            ;;
        self-signed|custom)
            # No additional validation needed
            ;;
        *)
            print_message "ERROR" "Unsupported certificate provider: $cert_provider"
            return 1
            ;;
    esac
    
    print_message "SUCCESS" "Certificate configuration is valid"
    return 0
}
