from django.http import HttpResponse


def create_file_shopping_cart(user, ingredients):
    """Создание файла с ингредиентами рецептов из корзины"""

    user_name = f"{user.first_name.title()}_" f"{user.last_name.title()}"
    shopping_list = f"Список покупок для: {user_name}\n\n"
    shopping_list += "\n".join(
        [
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ]
    )
    filename = f"{user.username}_shopping_list.txt"
    response = HttpResponse(shopping_list, content_type="text/plain")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
