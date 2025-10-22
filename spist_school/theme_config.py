"""
Enhanced Color Scheme and Theme System for SPIST
Green & Yellow School Colors with Dark Mode Support
"""

# SPIST Brand Colors
SPIST_COLORS = {
    # Primary Green Shades
    'forest_green': '#1B5E20',      # Darkest green
    'primary_green': '#2E7D32',     # Main brand green
    'medium_green': '#388E3C',      # Medium green
    'light_green': '#4CAF50',       # Light green
    'emerald': '#00C853',           # Bright accent
    'mint': '#A5D6A7',              # Very light green
    'lime': '#C5E1A5',              # Pale green
    
    # Yellow/Gold Shades
    'deep_gold': '#F57F17',         # Darkest yellow
    'primary_yellow': '#FBC02D',    # Main brand yellow
    'amber': '#FFC107',             # Warm yellow
    'light_yellow': '#FFEB3B',      # Bright yellow
    'gold': '#FFD54F',              # Light gold
    'cream': '#FFF9C4',             # Very light yellow
    
    # Neutral Grays (Light Mode)
    'gray_900': '#1A1A1A',
    'gray_800': '#2D2D2D',
    'gray_700': '#4A4A4A',
    'gray_600': '#6B6B6B',
    'gray_500': '#9E9E9E',
    'gray_400': '#BDBDBD',
    'gray_300': '#E0E0E0',
    'gray_200': '#EEEEEE',
    'gray_100': '#F5F5F5',
    'gray_50': '#FAFAFA',
    
    # Dark Mode Backgrounds
    'dark_bg_primary': '#0D1117',       # Main background
    'dark_bg_secondary': '#161B22',     # Card background
    'dark_bg_tertiary': '#21262D',      # Elevated elements
    'dark_bg_quaternary': '#2D333B',    # Hover states
    
    # Semantic Colors
    'success': '#00C853',
    'info': '#388E3C',
    'warning': '#FBC02D',
    'danger': '#E53935',
}

# Theme Configurations
LIGHT_THEME = {
    'name': 'light',
    'primary': SPIST_COLORS['primary_green'],
    'secondary': SPIST_COLORS['primary_yellow'],
    'background': '#F1F8E9',
    'surface': '#FFFFFF',
    'text_primary': '#1B5E20',
    'text_secondary': '#2E5233',
    'border': '#C5E1A5',
}

DARK_THEME = {
    'name': 'dark',
    'primary': SPIST_COLORS['light_green'],
    'secondary': SPIST_COLORS['gold'],
    'background': SPIST_COLORS['dark_bg_primary'],
    'surface': SPIST_COLORS['dark_bg_secondary'],
    'text_primary': '#E8F5E9',
    'text_secondary': '#C8E6C9',
    'border': '#2D333B',
}

# Component Color Mapping
COMPONENT_COLORS = {
    'button_primary': {
        'light': ('primary_green', 'light_green'),
        'dark': ('medium_green', 'light_green'),
    },
    'button_secondary': {
        'light': ('primary_yellow', 'light_yellow'),
        'dark': ('amber', 'gold'),
    },
    'card': {
        'light': 'white',
        'dark': 'dark_bg_secondary',
    },
    'navbar': {
        'light': ('primary_green', 'forest_green'),
        'dark': ('dark_bg_tertiary', 'dark_bg_quaternary'),
    },
}
