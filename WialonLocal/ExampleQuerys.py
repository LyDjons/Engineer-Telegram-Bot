query = (
    'svc=core/search_items&params={"spec":{'
    f'"itemsType":"avl_resource",'
    f'"propName":"reporttemplates",'
    f'"propValueMask":"*",'
    f'"sortType":"reporttemplates",'
    f'"propType":"propitemname",'
    f'"or_logic":"0"'
    '},'
    f'"force":"1",'
    f'"flags":"8193",'
    f'"from":"0",'
    f'"to":"100000"'
    '}'
)  # список всіх ресурсі і звітів в них
# print(session._simple_query_str(query))

query2 = (
    'svc=core/search_items&params={"spec":{'
    f'"itemsType":"avl_unit",'
    f'"propName":"rel_user_creator_name,rel_hw_type_name,sys_name",'
    f'"propValueMask":"SAgro,*Bi 920*,*John*",'
    f'"sortType":"avl_unit",'
    f'"propType":"rel_user_creator_name,rel_hw_type_name,sys_name",'
    f'"or_logic":"0"'
    '},'
    f'"force":"1",'
    f'"flags":"1",'
    f'"from":"0",'
    f'"to":"100000"'
    '}'
)  # Пошук обєктів за багатьма критеріями, "творець", "обладнання", маска імя
# print(session._simple_query_str(query2))

query_batch_1 = (
    'svc=core/batch&params={'
    '"params":[{'
    '"svc":"core/search_items",'
    '"params":{'
    '"spec":{'
    f'"itemsType":"avl_unit",'
    f'"propName":"sys_name",'
    f'"propValueMask":"*John Deere S670*",'
    f'"sortType":"sys_name",'
    f'"propType":"sys_name",'
    f'"or_logic":"0"'
    '},'
    f'"force":"1",'
    f'"flags":"1",'
    f'"from":"0",'
    f'"to":"100000"'
    '}'

    ' },'
    '{'
    '"svc":"core/search_items",'
    '"params":{'
    '"spec":{'
    f'"itemsType":"avl_resource",'
    f'"propName":"reporttemplates",'
    f'"propValueMask":"10. Універс*",'
    f'"sortType":"reporttemplates",'
    f'"propType":"propitemname",'
    f'"or_logic":"0"'
    '},'
    f'"force":"1",'
    f'"flags":"1",'
    f'"from":"0",'
    f'"to":"100000"'
    '}'

    ' }'
    '],'
    '"flags": "1"'
    '}'
)  # пример с batch. Два запроса в одном
# print(session._simple_query_str(query_batch_1))