from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from .models import PlayerRegistration, Season, GeneralSettings, Payment

class PlayerRegistrationResource(resources.ModelResource):
    class Meta:
        model = PlayerRegistration
        fields = (
            'id', 'reg_id','user__username', 'player_name', 'father_name',
            'dob', 'gender', 'tshirt_size', 'mobile', 'wathsapp_number', 'email', 'adhar_card',
            'player_image', 'district', 'zone', 'pin_code', 'address', 'first_preference','batting_arm',
            'role', 'is_compleated', 'tx_id', 'is_selected', 'points','created'
        )
        export_order = fields
        
        import_id_fields = ['id']

class PlayerRegistrationAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('season_title', 'reg_id', 'player_name', 'district', 'zone', 'is_compleated', 'points', 'created')
    
    search_fields = (
        'reg_id', 'user__username', 'player_name', 'mobile',
        'email', 'adhar_card', 'district','tx_id', "is_selected", "points"
    )
    list_filter = ('zone', 'is_compleated','is_selected', 'gender', 'district')
    ordering = ('-created',)
    readonly_fields = ('reg_id','zone', 'created')
    
    resource_class = PlayerRegistrationResource  

    def season_title(self, obj):
        return obj.season.title if obj.season else "-"
    
    season_title.short_description = "Season"   # Column name in admin UI

    
admin.site.register(PlayerRegistration, PlayerRegistrationAdmin)
admin.site.register(Season)
admin.site.register(GeneralSettings)
admin.site.register(Payment)