# PyProject

A simple PySide6 tool to create python projects from templates.

It allows the setting of default packages as well as python version and extra setup templates (such as direnv files etc).

It is designed to be used with the [uv](https://docs.astral.sh/uv/) tool for managing python projects and virtual environments and is intended to help students new to python get started with some of the more complex projects we do (for example Jupyter ML projects etc).

# JSON Configuration

This JSON format is designed to describe project configurations for Python-based projects, specifying packages, descriptions, and extra settings. Each top-level key represents a project profile (e.g., `"nccapy project"`, `"ML Project"`).

### Top-Level Structure

- **Project Name (string)**:
  Each key at the top level is the name of a project configuration. The value is an object with the following fields:

#### Fields

- **packages** (`array` of `array`):
  Lists the packages to be installed for the project. Each package entry is an array:
  - `[package_name, status, (optional) version_spec]`
    - `package_name` (string): Name of the package (e.g., `"numpy"`).
    - `status` (string): `"enabled"` or `"disabled"`.
    - `version_spec` (string, optional): Version requirement (e.g., `">=1.2.3"`).

- **description** (`array` of `string`):
  A list of strings describing the project, its purpose, and any relevant notes.

- **extras** (`object`, optional):
  Additional configuration options. Example:
  - `templates` (`array` of `string`): List of template-related files or notes.

- **pyproject_extras** (`array` of `string`, optional):
  Additional lines or blocks to be included in the `pyproject.toml` or similar configuration files. These are typically TOML-formatted strings for advanced configuration (e.g., custom package indexes, dependency groups).

The schema is as follows

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "patternProperties": {
    "^.*$": {
      "type": "object",
      "properties": {
        "packages": {
          "type": "array",
          "items": {
            "type": "array",
            "minItems": 2,
            "maxItems": 3,
            "items": [
              { "type": "string" },         // package name
              { "type": "string", "enum": ["enabled", "disabled"] }, // status
              { "type": "string" }          // version spec (optional)
            ]
          }
        },
        "description": {
          "type": "array",
          "items": { "type": "string" }
        },
        "extras": {
          "type": "object",
          "properties": {
            "templates": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "additionalProperties": true
        },
        "pyproject_extras": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["packages", "description"],
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```
