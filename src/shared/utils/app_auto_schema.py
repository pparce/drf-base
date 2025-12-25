from drf_spectacular.openapi import AutoSchema

class AppNameAutoSchema(AutoSchema):
    def get_tags(self):
        # Extrae el nombre de la aplicación del `ViewSet` para usarlo como tag
        if hasattr(self.view, 'basename'):
            app_name = self.view.basename.split('_')[0].capitalize()
            return [app_name]
        return super().get_tags()