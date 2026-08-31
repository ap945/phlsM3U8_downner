# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in phlsM3U8_downner, please report
it privately via [GitHub Security Advisories](https://github.com/AP945/phlsM3U8_downner/security/advisories/new).

Please **do not** open a public Issue for security reports.

You can expect an initial response within **7 days**.

## Scope Notes

- This tool downloads and decrypts HLS/m3u8 streams. Treat input URLs and
  AES-128 key files as untrusted input.
- SSL certificate verification is **disabled by default** (`verify_ssl=False`)
  because many target sites have broken certificates. Enable it in
  `config_set` if you only download from trusted hosts.
