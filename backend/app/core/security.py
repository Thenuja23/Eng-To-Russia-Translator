class SecurityUtils:
    def check_magic_bytes(self, data, expected):
        if len(data) < len(expected):
            return False
        return data[:len(expected)] == expected

    def check_size(self, size_bytes, max_mb=10):
        return size_bytes <= max_mb * 1024 * 1024

    def check_page_limit(self, pages, max_pages=50):
        return pages <= max_pages
