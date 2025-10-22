# GitHub-Inspired Theme Guide for Insights Dashboard

## Overview

The Insights dashboard now features a modern, GitHub-inspired design with support for both dark and light themes. The interface has been completely redesigned to provide a cleaner, more professional look while maintaining all existing functionality.

## Features

### Visual Design
- **GitHub-inspired color palette**: Uses GitHub's official color scheme for both dark and light themes
- **Modern typography**: System font stack matching GitHub (`-apple-system, BlinkMacSystemFont, "Segoe UI", etc.`)
- **Clean layout**: Card-based design with consistent spacing and subtle shadows
- **Professional aesthetics**: Follows GitHub's design principles for clarity and usability

### Navigation
- **Sidebar navigation**: Left-side menu with all main sections
- **Top navbar**: Fixed header with branding and theme toggle
- **Active state indicators**: Clear visual feedback for current section
- **Responsive design**: Mobile-friendly layout that adapts to screen size

### Themes

#### Dark Theme (Default)
The dark theme uses GitHub's dark color scheme:
- Background: `#0d1117` (canvas-default)
- Surface: `#161b22` (canvas-subtle)
- Text: `#e6edf3` (foreground-default)
- Accent: `#2f81f7` (accent-blue)
- Borders: `#30363d` (border-default)

#### Light Theme
The light theme uses GitHub's light color scheme:
- Background: `#ffffff` (canvas-default)
- Surface: `#f6f8fa` (canvas-subtle)
- Text: `#1f2328` (foreground-default)
- Accent: `#0969da` (accent-blue)
- Borders: `#d0d7de` (border-default)

## Using Theme Toggle

### Switching Themes

1. **Locate the theme toggle button**
   - Find the button in the top-right corner of the navigation bar
   - It displays a moon emoji (🌙) for dark theme or sun emoji (☀️) for light theme

2. **Click to toggle**
   - Click the button once to switch between themes
   - The theme change is instant and affects the entire dashboard

3. **Theme persistence**
   - Your theme choice is saved in browser local storage
   - The selected theme will be remembered on your next visit

### Programmatic Theme Control

The theme is controlled through CSS variables and can be customized:

```css
/* Dark theme (default) */
:root {
    --gh-canvas-default: #0d1117;
    --gh-canvas-subtle: #161b22;
    --gh-fg-default: #e6edf3;
    /* ... more variables */
}

/* Light theme */
[data-theme="light"] {
    --gh-canvas-default: #ffffff;
    --gh-canvas-subtle: #f6f8fa;
    --gh-fg-default: #1f2328;
    /* ... more variables */
}
```

## Components

All dashboard components have been styled to match the GitHub theme:

### Cards
- Subtle background with border
- Consistent padding and rounded corners
- Clean header separation

### Buttons
- GitHub-style primary, secondary, and danger buttons
- Hover states with subtle transitions
- Small, medium, and large sizes available

### Tables
- Hover effects on rows
- Clean borders and spacing
- GitHub issue/PR list aesthetics

### Forms
- Consistent input styling
- Focus states with accent color
- Proper label hierarchy

### Alerts and Badges
- Color-coded for different states (success, warning, danger, info)
- Subtle backgrounds with contrasting text
- Rounded corners matching GitHub style

## Layout Structure

```
┌─────────────────────────────────────────────┐
│ Top Navbar (Fixed)                          │
│ Logo | Repo Name              | Theme Toggle│
├──────────┬──────────────────────────────────┤
│          │                                  │
│ Sidebar  │  Main Content Area               │
│ Nav      │                                  │
│ Menu     │  (Cards, Tables, Graphs, etc.)   │
│          │                                  │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

## Responsive Behavior

### Desktop (> 1024px)
- Full sidebar visible
- Wide content area
- All features accessible

### Tablet (768px - 1024px)
- Narrower sidebar (220px)
- Adjusted content width
- Maintained functionality

### Mobile (< 768px)
- Collapsible sidebar
- Full-width content
- Touch-friendly navigation

## Customization

### Changing Colors

Edit `assets/github-theme.css` and modify the CSS variables in the `:root` selector:

```css
:root {
    --gh-accent-fg: #2f81f7;  /* Change accent color */
    --spacing-3: 16px;         /* Adjust spacing */
    /* ... more variables */
}
```

### Adding Custom Styles

Add your custom styles to the end of `assets/github-theme.css` or create a new CSS file in the assets directory.

### Icon Customization

Unicode emoji icons are currently used for simplicity. To use custom SVG icons:

1. Edit `assets/icons.py`
2. Update the icon functions with your SVG code
3. Use the icon functions in the dashboard layout

## Best Practices

1. **Maintain consistency**: Use the defined CSS variables for colors and spacing
2. **Follow GitHub patterns**: Reference GitHub's UI for new components
3. **Test both themes**: Ensure all changes work in both dark and light mode
4. **Respect accessibility**: Maintain proper contrast ratios
5. **Keep it responsive**: Test on different screen sizes

## Troubleshooting

### Theme not changing
- Clear browser cache
- Check browser console for errors
- Verify `assets/github-theme.css` is loaded

### Colors look wrong
- Check if custom styles are overriding theme variables
- Verify CSS variable names match the theme definition
- Ensure `data-theme` attribute is being set correctly

### Layout issues on mobile
- Check responsive CSS media queries
- Verify viewport meta tag is present
- Test on actual mobile devices or browser dev tools

## Migration from Old Design

The redesign maintains backward compatibility with all existing Dash components. No changes to Python code are required for basic functionality. However, to fully leverage the new design:

1. Review component styling in your tabs
2. Use `className` props to apply GitHub theme classes
3. Replace inline styles with theme CSS classes where appropriate
4. Test all interactive features in both themes

## Support

For issues or questions about the theme:
- Check the CSS file comments in `assets/github-theme.css`
- Review the dashboard layout in `dashboard/dashboard_ui.py`
- Refer to GitHub's own design system for inspiration

## Future Enhancements

Planned improvements:
- [ ] SVG icon system (replacing emoji)
- [ ] Additional theme variants (e.g., high contrast)
- [ ] Theme customization panel in settings
- [ ] Saved theme preferences per user
- [ ] Accessibility improvements (WCAG AAA compliance)
- [ ] Animation and transition refinements
