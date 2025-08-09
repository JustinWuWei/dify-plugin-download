# Download - File downloader

**Author:** [bowenliang123](https://github.com/bowenliang123)

**Github Repository:** https://github.com/bowenliang123/dify-plugin-download

**Dify Marketplace:** https://marketplace.dify.ai/plugins/bowenliang123/download

## Overview

Download files from give URLs to Dify files.

## Key Features

- 🚀 **HTTP Download files from URL**
- 🌊 **Streaming file downloading**
- 💰 **Concurrent support for multiple files downloading**
- ⚡ ** Support GET / POST methods with custom body and headers**
- 🎨 **Custom output filenames**
- 🔄 **HTTP redirection auto-handling**
- 🌟 **Timout controls and SSL certificate verification options**

## Tool Descriptions

### Download Single File

- tool: `single_file_download`
- inputs:
    - URL to download file from
    - Optional: custom filename for the downloaded file

![single_file_download_1.png](_assets/single_file_download_1.png)

### Download Multiple Files

- tool: `multiple_file_download`
- inputs:
    - URLs to download file from, one URL per line
    - Optional: custom filename for the downloaded files, one filename per line

![multiple_file_download_1.png](_assets/multiple_file_download_1.png)
multiple_file_download_1.png

---

## Changelog

- 0.0.1:
    - add `single_file_download` and `multiple_file_download` tool, support downloading single and multiple file from
      URL(s)
    - support HTTP 301/302 redirection
    - support enabling / disabling SSL certificate verification

## License

- Apache License 2.0

## Privacy

This plugin collects no data.

All the file transformations are completed locally. NO data is transmitted to third-party services.

