import os
import time
from shelflet import Model, CharField, AutoField, DateTimeField, DateField, TimeField
from datetime import datetime, date, timedelta

# Clean up previous test files
for file in ["test_all_fixes.db", "autofield_counter.dat"]:
    for ext in ["", ".bak", ".dat", ".dir"]:
        try:
            os.remove(file + ext)
        except FileNotFoundError:
            pass

# Model with all the fields we've modified
class AllFixesModel(Model):
    name = CharField(required=True, unique=True)
    auto_field = AutoField()
    created_at = DateTimeField()
    event_date = DateField(min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
    event_time = TimeField()
    db_file = "test_all_fixes.db"

# Initialize
AllFixesModel.open(index=True)

print("=== Testing AutoField ===")
# Create first instance
obj1 = AllFixesModel(name="Test1", created_at=datetime.now(), 
                event_date=date.today(), event_time=datetime.now().time())
obj1.save()
print(f"First object auto_field: {obj1.auto_field}")

# Create second instance
obj2 = AllFixesModel(name="Test2", created_at=datetime.now(), 
                event_date=date.today(), event_time=datetime.now().time())
obj2.save()
print(f"Second object auto_field: {obj2.auto_field}")

# Verify counter is saved to file
print(f"Counter file exists: {os.path.exists('autofield_counter.dat')}")
with open('autofield_counter.dat', 'r') as f:
    counter = int(f.read().strip())
    print(f"Saved counter value: {counter}")
    assert counter == obj2.auto_field, "Counter should match the last auto_field value"

print("\n=== Testing Unique Constraint ===")
# Test unique constraint
try:
    # Try to create an object with the same name (should fail)
    duplicate = AllFixesModel(name="Test1", created_at=datetime.now(), 
                         event_date=date.today(), event_time=datetime.now().time())
    duplicate.save()
    print("ERROR: Unique constraint failed!")
except ValueError as e:
    print(f"Unique constraint works: {e}")

print("\n=== Testing Date/Time Validation ===")
# Test date validation
try:
    # Try to create an object with an invalid date (before min_value)
    invalid_date = AllFixesModel(name="Test3", created_at=datetime.now(), 
                            event_date=date(1999, 12, 31), event_time=datetime.now().time())
    invalid_date.save()
    print("ERROR: Date validation failed!")
except ValueError as e:
    print(f"Date validation works: {e}")

try:
    # Try to create an object with an invalid date (after max_value)
    invalid_date = AllFixesModel(name="Test3", created_at=datetime.now(), 
                            event_date=date(2101, 1, 1), event_time=datetime.now().time())
    invalid_date.save()
    print("ERROR: Date validation failed!")
except ValueError as e:
    print(f"Date validation works: {e}")

print("\n=== Testing AutoField Persistence ===")
# Close and reopen to simulate application restart
AllFixesModel.open(index=False)  # Reset cache
AllFixesModel._index_cache = None

# Create another instance after "restart"
obj3 = AllFixesModel(name="Test3", created_at=datetime.now(), 
                event_date=date.today(), event_time=datetime.now().time())
obj3.save()
print(f"Third object auto_field after 'restart': {obj3.auto_field}")
assert obj3.auto_field > obj2.auto_field, "AutoField should continue counting after restart"

print("\nAll tests passed successfully!")
