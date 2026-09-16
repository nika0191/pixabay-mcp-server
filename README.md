# Pixabay MCP Server

A Model Context Protocol (MCP) server that provides access to the Pixabay API for searching and retrieving royalty-free images and videos.

📖 **[Complete Setup and Usage Guide](https://unlockmcp.com/guides/pixabay-mcp-server-complete-setup-guide/)** - Step-by-step tutorial with examples and troubleshooting

## Features

- **Image Search**: Search through millions of royalty-free images
- **Video Search**: Find high-quality stock videos
- **Advanced Filtering**: Filter by category, orientation, color, size, and more
- **Individual Lookup**: Get specific images or videos by ID
- **Multiple Formats**: Access different image sizes and video qualities

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd pixabay-mcp-server
```

2. Install dependencies:
```bash
npm install
```

3. Build the project:
```bash
npm run build
```

## Configuration

### API Key Setup

You'll need a Pixabay API key to use this server:

1. Sign up at [Pixabay](https://pixabay.com/accounts/register/)
2. Go to [Pixabay API page](https://pixabay.com/api/docs/)
3. Get your API key
4. **Set the system environment variable** (recommended for security):

**For bash/zsh** (add to ~/.bashrc, ~/.zshrc, or ~/.bash_profile):
```bash
export PIXABAY_API_KEY="your-api-key-here"
```

**For fish** (add to ~/.config/fish/config.fish):
```fish
set -gx PIXABAY_API_KEY "your-api-key-here"
```

**For Windows** (Command Prompt):
```cmd
setx PIXABAY_API_KEY "your-api-key-here"
```

After setting the environment variable, restart your terminal or run:
```bash
source ~/.zshrc  # or your shell's config file
```

### Claude Desktop Configuration

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Recommended (using system environment variable):**
```json
{
  "mcpServers": {
    "pixabay": {
      "command": "node",
      "args": ["/path/to/pixabay-mcp-server/dist/index.js"]
    }
  }
}
```

**Alternative (less secure - API key in config file):**
```json
{
  "mcpServers": {
    "pixabay": {
      "command": "node",
      "args": ["/path/to/pixabay-mcp-server/dist/index.js"],
      "env": {
        "PIXABAY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Security Note**: The recommended approach uses your system environment variable, keeping the API key out of configuration files.

## Available Tools

### search_images
Search for royalty-free images with various filters:

- `q`: Search term (max 100 characters)
- `lang`: Language code (default: "en")
- `image_type`: "all", "photo", "illustration", "vector"
- `orientation`: "all", "horizontal", "vertical"
- `category`: Category filter (nature, business, etc.)
- `min_width`/`min_height`: Minimum dimensions
- `colors`: Color filter (red, blue, grayscale, etc.)
- `editors_choice`: Editor's Choice awards only
- `safesearch`: Safe for all ages
- `order`: "popular" or "latest"
- `page`: Page number (default: 1)
- `per_page`: Results per page (3-200, default: 20)

### search_videos
Search for royalty-free videos with similar filtering options:

- `q`: Search term
- `video_type`: "all", "film", "animation"
- All other parameters similar to image search

### get_image_by_id
Retrieve a specific image by its Pixabay ID:
- `id`: Pixabay image ID (required)

### get_video_by_id
Retrieve a specific video by its Pixabay ID:
- `id`: Pixabay video ID (required)

## Usage Examples

### Basic Image Search
```
Search for "mountain landscape" photos
```

### Advanced Image Search
```
Search for horizontal nature photos with minimum width 1920px, editors choice only
```

### Video Search
```
Find animation videos about "space exploration"
```

## Claude Code Skill: Video Producer

This repo also ships a [Claude Code skill](.claude/skills/pixabay-video-producer/SKILL.md)
that turns a script or topic into a finished MP4 built from real (non-AI)
Pixabay footage: it searches Pixabay per scene, filters out AI-generated and
low-quality clips, downloads them, and assembles the result with `ffmpeg`
into a vertical/horizontal/square cut with optional crossfades and a
music/voiceover track. Requires `PIXABAY_API_KEY` plus `ffmpeg`/`ffprobe` on
PATH; see the skill file for the full workflow.

## API Rate Limits

- 100 requests per 60 seconds by default
- Responses must be cached for 24 hours
- Systematic mass downloads are not allowed

## Response Format

The server returns JSON responses with image/video metadata including:
- URLs for different sizes
- Dimensions and file sizes
- View/download/like counts
- User information
- Tags and categories

## Development

### Running in Development Mode
```bash
npm run dev
```

### Building
```bash
npm run build
```

### Testing
```bash
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Author

Created by [UnlockMCP](https://unlockmcp.com) - Your guide to mastering Model Context Protocol implementations.

## License

MIT License - see LICENSE file for details

## Disclaimer

This server provides access to Pixabay's API. Please comply with:
- Pixabay's Terms of Service
- Content License requirements
- Attribution requirements when displaying search results
- Rate limiting and caching requirements

Images and videos are subject to Pixabay's Content License. Always check individual image/video licenses before use.