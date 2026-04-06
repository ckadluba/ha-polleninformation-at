#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
config_dir="${workspace_dir}/.devcontainer/config"
custom_components_dir="${config_dir}/custom_components"
integration_link="${custom_components_dir}/polleninformation_at"
integration_source="${workspace_dir}/custom_components/polleninformation_at"

mkdir -p "${custom_components_dir}"

if [[ -L "${integration_link}" || -e "${integration_link}" ]]; then
  rm -rf "${integration_link}"
fi

ln -s "${integration_source}" "${integration_link}"

