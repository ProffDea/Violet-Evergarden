class menu:
    def __init__(self, options):
        self.options = {
            "quit": self.quit
        }

    def template(self):
        return f"```py\n'Menu Title' - Info\n```\n1.) Option 1\n2.) Option 2\n3.) Option 3\n4.) Option 4\n\n```py\n# Notes\nEnter 'quit' to close menu\n```"

    def quit(self):
        return "Menu has been closed"

    def timeout(self):
        return "Menu has been closed due to timeout"