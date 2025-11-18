# Muset Frontend

AI Writing Assistant Frontend built with Next.js 15 and React 19.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Emotion
- **UI Components**: Radix UI
- **Icons**: Phosphor Icons
- **Rich Text Editor**: TipTap
- **State Management**: Zustand
- **HTTP Client**: Fetch API

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp ../.env.example .env.local
```

3. Start development server:
```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                  # Next.js app router
│   ├── (auth)/          # Auth-related pages
│   ├── (dashboard)/     # Dashboard pages
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page
├── components/           # React components
│   ├── editor/          # Editor components
│   ├── chat/            # Chat interface
│   ├── ui/              # Reusable UI components
│   └── ...
├── lib/                 # Utilities and helpers
│   ├── api.ts           # API client
│   ├── stores/          # Zustand stores
│   └── utils.ts         # Helper functions
├── styles/              # Global styles
├── public/              # Static assets
└── package.json
```

## Development

### Code Quality

Format code:
```bash
npm run format
```

Run linter:
```bash
npm run lint
```

### Build

Build for production:
```bash
npm run build
```

Start production server:
```bash
npm run start
```

## Features

- Rich text editor with AI assistance
- Real-time chat interface
- File management and version history
- Project and workspace management
- MCP server configuration
- Claude Skills integration
- Multi-language support
