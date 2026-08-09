# Security Policy

## Supported Versions

Only the latest major release of LocalHub receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x (V2) | :white_check_mark: |
| < 0.2.0 | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in LocalHub, **please do not open a public issue**.

Instead, please report it privately to our team:
- **Email**: [ayanabha.c@aol.com](mailto:ayanabha.c@aol.com)

Please include the following details in your report:
- Type of issue (e.g. path traversal, auth bypass, session leaks)
- Step-by-step instructions to reproduce the issue
- Affected components or versions
- Any potential mitigation or fix if known

We will acknowledge receipt of your vulnerability report within 48 hours and provide regular updates on the resolution.

## Security Best Practices for LocalHub Users

LocalHub is designed for temporary, peer-to-peer local project collaboration. To maintain a secure environment:
1. **Never commit `.env` files**: Ensure `.env` containing sensitive tokens or credentials is listed in `.gitignore`. Use `.env.example` as a safe template.
2. **Review Access Requests**: Always inspect the username/identity before approving collaborator requests on the Owner Command Center (`/admin`).
3. **Terminate Sessions Promptly**: Run `localhub stop` immediately when collaboration is complete to close public Cloudflare tunnels and shut down local endpoints.
4. **Environment Passwords**: Set `LOCALHUB_ADMIN_PASSWORD` in your `.env` file to protect the Owner Command Center endpoints when running in shared local networks.
