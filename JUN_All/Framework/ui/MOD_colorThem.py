class ColorTheme:
    def __init__(self, name, **colors):
        self.name = name
        self.colors = colors

    def get(self, key, default=None):
        return self.colors.get(key, default)

    def as_dict(self):
        return dict(self.colors)
    
class ColorThemeRegistry:
    _themes = {}

    @classmethod
    def register(cls, theme: ColorTheme):
        cls._themes[theme.name] = theme

    @classmethod
    def get(cls, name):
        if name not in cls._themes:
            raise KeyError(f"Color theme not found: {name}")
        return cls._themes[name]

    @classmethod
    def list_themes(cls):
        return list(cls._themes.keys())
    
# Dark Indigo
ColorThemeRegistry.register(
    ColorTheme(
        "dark_indigo",
        color_mainDark=[0.10, 0.12, 0.18],
        color_main=[0.14, 0.17, 0.25],
        color_sub=[0.18, 0.22, 0.32],
        color_btn=[0.30, 0.35, 0.45],
        color_back=[0.12, 0.14, 0.20],
    )
)

# Green 01
ColorThemeRegistry.register(
    ColorTheme(
        "green_01",
        color_mainDark=[0.0, 0.2, 0.0],
        color_main=[0.3, 0.65, 0.2],
        color_sub=[0.3, 0.6, 0.1],
        color_btn=[0.95, 0.7, 0.5],
        color_back=[0.96, 0.96, 0.96],
    )
)

# coral 01
ColorThemeRegistry.register(
    ColorTheme(
        "coral_01",
        color_mainDark = [0.65, 0.4, 0.4],
        color_main = [0.824, 0.457, 0.039],
        color_sub = [0.937, 0.597, 0.488],
        color_btn = [1.0, 0.8, 0.7],
        color_back = [1.0, 0.761, 0.6289],
    )
)

# blue 01
ColorThemeRegistry.register(
    ColorTheme(
        "blue_01",
        color_mainDark = [0.1, 0.15, 0.45],
        color_main     = [0.0, 0.45, 0.75],
        color_sub      = [0.4, 0.7, 0.9],
        color_btn      = [0.7, 0.9, 1.0],
        color_back     = [0.85, 0.95, 1.0]   ,
    )
)

# purple 01
ColorThemeRegistry.register(
    ColorTheme(
        "purple_01",
        color_mainDark = [0.0, 0.0, 0.30],
        color_main = [0.3, 0.1, 0.5],
        color_sub = [0.4, 0.3, 0.7],
        color_btn = [0.95, 0.2, 0.7],
        color_back = [0.96, 0.96, 0.96],
    )
)

## example

class Example_color:
    def __init__(self):
        theme_name="dark_indigo"

        theme = ColorThemeRegistry.get(theme_name)

        self.color_mainDark = theme.get("color_mainDark")
        self.color_main     = theme.get("color_main")
        self.color_sub      = theme.get("color_sub")
        self.color_btn      = theme.get("color_btn")
        self.color_back     = theme.get("color_back")

        self.color_all = theme.as_dict()