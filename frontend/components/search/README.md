# Global Search Component

Comprehensive search functionality with keyboard shortcuts, search history, and result highlighting.

## Features

- 🔍 Full-text search across pages, chat messages, and files
- ⌨️ Keyboard shortcut support (Cmd/Ctrl + K)
- 📝 Search history tracking
- 🎨 Syntax highlighting for search terms
- 🔄 Real-time search with debouncing
- 🏷️ Content type filtering
- ⌨️ Keyboard navigation (Arrow keys, Enter, Esc)
- 🌙 Dark mode support

## Components

### SearchModal

Main modal component that orchestrates the search experience.

**Props:**
- `isOpen` (boolean): Whether the modal is open
- `onClose` (function): Callback when modal closes
- `workspaceId` (string): Current workspace ID

### SearchInput

Search input with content type filters.

### SearchResults

Displays search results with keyboard navigation.

### SearchResultItem

Individual search result with syntax highlighting.

### SearchHistory

Shows recent searches with timestamps.

## Usage

### Basic Integration

```typescript
"use client";

import { SearchModal } from "@/components/search";
import { useGlobalSearch } from "@/lib/hooks/useGlobalSearch";

export default function App() {
  const { isOpen, closeSearch } = useGlobalSearch();
  const workspaceId = "your-workspace-id"; // Get from your app state

  return (
    <>
      {/* Your app content */}
      <div>
        <h1>My App</h1>
        {/* Search is triggered automatically with Cmd/Ctrl + K */}
      </div>

      {/* Search Modal */}
      <SearchModal
        isOpen={isOpen}
        onClose={closeSearch}
        workspaceId={workspaceId}
      />
    </>
  );
}
```

### With Manual Trigger

```typescript
"use client";

import { SearchModal } from "@/components/search";
import { useGlobalSearch } from "@/lib/hooks/useGlobalSearch";

export default function AppWithButton() {
  const { isOpen, openSearch, closeSearch } = useGlobalSearch();
  const workspaceId = "your-workspace-id";

  return (
    <>
      {/* Manual trigger button */}
      <button onClick={openSearch}>
        Open Search (Cmd+K)
      </button>

      {/* Search Modal */}
      <SearchModal
        isOpen={isOpen}
        onClose={closeSearch}
        workspaceId={workspaceId}
      />
    </>
  );
}
```

### In Layout Component

```typescript
// app/layout.tsx or app/[workspaceId]/layout.tsx
"use client";

import { SearchModal } from "@/components/search";
import { useGlobalSearch } from "@/lib/hooks/useGlobalSearch";
import { useParams } from "next/navigation";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isOpen, closeSearch } = useGlobalSearch();
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  return (
    <html lang="en">
      <body>
        {children}

        {/* Global search modal - available everywhere */}
        {workspaceId && (
          <SearchModal
            isOpen={isOpen}
            onClose={closeSearch}
            workspaceId={workspaceId}
          />
        )}
      </body>
    </html>
  );
}
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + K` | Open/close search modal |
| `Esc` | Close search modal |
| `↑` / `↓` | Navigate through results |
| `Enter` | Select highlighted result |

## Customization

### Styling

The search components use Tailwind CSS and support dark mode. Customize by modifying the className props.

### Content Type Icons

Icons can be customized in `SearchResultItem.tsx`:

```typescript
function getContentTypeIcon(contentType: string): string {
  switch (contentType) {
    case "page":
      return "📄";
    case "chat_message":
      return "💬";
    case "file":
      return "📁";
    default:
      return "📋";
  }
}
```

### Search Debounce

Default debounce time is 300ms. Adjust in `SearchModal.tsx`:

```typescript
const timer = setTimeout(() => {
  if (query) {
    performSearch(query);
  }
}, 300); // Change this value
```

## API Integration

The search component requires the following API endpoints (already implemented in backend):

- `POST /api/v1/search/workspaces/{id}/search` - Perform search
- `GET /api/v1/search/workspaces/{id}/search/history` - Get search history

See `lib/api/search.ts` for full API client implementation.

## Examples

### With Zustand Store

```typescript
import { create } from "zustand";

interface SearchStore {
  isSearchOpen: boolean;
  openSearch: () => void;
  closeSearch: () => void;
}

export const useSearchStore = create<SearchStore>((set) => ({
  isSearchOpen: false,
  openSearch: () => set({ isSearchOpen: true }),
  closeSearch: () => set({ isSearchOpen: false }),
}));

// In component
function MyComponent() {
  const { isSearchOpen, closeSearch } = useSearchStore();
  return <SearchModal isOpen={isSearchOpen} onClose={closeSearch} workspaceId="..." />;
}
```

## Testing

See `__tests__/search.test.tsx` for component tests (TODO: Create test file).

## Accessibility

- Full keyboard navigation support
- ARIA labels for screen readers
- Focus management
- Escape key to close

## Browser Support

- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- Mobile browsers: ✅ (touch-friendly)

## Performance

- Debounced search (300ms)
- Lazy loading of search history
- Efficient keyboard event handling
- Memoized highlight rendering

## Future Enhancements

- [ ] Voice search
- [ ] Advanced filters (date range, author)
- [ ] Search suggestions
- [ ] Recent results cache
- [ ] Search analytics
