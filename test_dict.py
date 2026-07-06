attributes = {"image_urls": ["url1", "url2", "url3"], "foo": "bar"}
new_attrs = {"transaction_type": "Sale"}
attributes.update(new_attrs)
print(attributes)
