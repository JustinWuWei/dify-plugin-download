# Download - Full-featured File Downloader

**Author:** [bowenliang123](https://github.com/bowenliang123)

**Github Repository:** https://github.com/bowenliang123/dify-plugin-download

**Dify Marketplace:** https://marketplace.dify.ai/plugins/bowenliang123/download

## Overview

Download files from URL, with support of concurrent downloading, streaming transporting, proxy, keep-alive, custom file names, HTTP redirection, timeout controls and SSL certificate configs.

## Key Features

- 🔁 **Keep-Alive & Connection Pooling by default**
- 🌊 **Streaming Downloads**
- 💫 **Concurrent Downloads with failing-fast handling**
- 🚀 **HTTP/1.1 and HTTP/2 Support**
- ⚡ **GET / POST method with custom request body**
- 🎨 **Custom output filenames**
- 🌼 **Custom HTTP headers**
- 🏖️ **HTTP(S) / SOCKS proxy support**
- 🧭 **HTTP redirection auto-handling**
- 📚 **Automatic Decompression support of Gzip / Brotli / Zstd**
- 🌟 **Connection Timeouts controls**
- ✨ **SSL certificate verification options**

## Tool Descriptions

### Download Single File

- tool: `single_file_download`
- inputs:
    - URL to download file from
    - Optional:
        - custom filename for the downloaded file
        - HTTP method to use, either `GET` or `POST`
        - HTTP headers in JSON format, one header per line
        - Proxy URL, supporting `http://`, `https://`, `socks5://`
        - enable or disable SSL certificate verification

![single_file_download_1.png](_assets/single_file_download_1.png)

### Download Multiple Files

- tool: `multiple_file_download`
- inputs:
    - URLs to download file from, one URL per line
    - Request Timeout in seconds
    - Optional:
        - Custom filename for the downloaded files, one filename per line
        - HTTP method to use, either `GET` or `POST`
        - HTTP headers in JSON format, one header per line
        - Proxy URL, supporting `http://`, `https://`, `socks5://`
        - enable or disable SSL certificate verification

![multiple_file_download_1.png](_assets/multiple_file_download_1.png)
multiple_file_download_1.png

---

## Changelog

- 0.5.0:
    - support connection pooling with keep-alive support
    - ensure the output files tool in correct order of index in `multiple_file_download`

- 0.4.0:
    - fix custom filenames for multiple file downloads

- 0.3.0:
    - support concurrent downloads with failing-fast handling
    - lower the default request timeout to 5 seconds
    - fix custom filenames for multiple file downloads

- 0.2.0:
    - temporarily falling back from concurrent downloads to synchronous downloads

- 0.1.0:
    - add `single_file_download` and `multiple_file_download` tool, support downloading single and multiple file from
      URL(s)
    - support HTTP 301/302 redirection
    - support enabling / disabling SSL certificate verification

## License

- Apache License 2.0

## Privacy

This plugin collects no data.

All the file transformations are completed locally. NO data is transmitted to third-party services.

