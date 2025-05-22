from shelflet import Model, CharField, AutoField

# Model for testing AutoField
class AutoFieldModel(Model):
    name = CharField(required=True)
    auto_field = AutoField()
    db_file = "test_autofield.db"

# Initialize
AutoFieldModel.open(index=True)

# Create an instance
obj = AutoFieldModel(name="Test")
obj.save()

# Check if auto_field is not None
print(f"Auto field value: {obj.auto_field}")
assert obj.auto_field is not None, "Auto field should not be None"

# Get from database and check again
saved = AutoFieldModel.get_by_id(obj.id)
print(f"Saved auto field value: {saved.auto_field}")
assert saved.auto_field is not None, "Saved auto field should not be None"

print("Test passed! AutoField is working correctly.")
