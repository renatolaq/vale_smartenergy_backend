# returns queryset with one attribute as string
def queryset_name_to_string(queryset):
    result = ""
    for name in queryset:
        if result != "":
            result += ", "
        result += name[0]
    return result
