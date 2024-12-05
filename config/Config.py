class Config:
    def __init__(self):
        self.window_size = (800,600)
        self.view_mode_value = 4
        self.wrap_mode_active = False
        self.font_size = 16
        self.encoding_files = "utf-8"
        self.tab_size = 4
        
        self.keep_console_open = True
    
    def get_config(self):
        pass
    
    
    
config = Config()