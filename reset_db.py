from app import app, db, Farm, SoilRecord, Harvest, SoilValue

print("Resetting the dashboard data...")

# Initialize the app context
with app.app_context():
    print("Deleting all soil records and harvests...")

    # Delete all soil values first (to avoid foreign key constraints)
    SoilValue.query.delete()

    # Delete all soil records
    SoilRecord.query.delete()

    # Delete all harvests
    Harvest.query.delete()

    # Commit the changes
    db.session.commit()

    print("All soil records and harvests have been deleted.")

    # Verify the deletion
    soil_record_count = SoilRecord.query.count()
    harvest_count = Harvest.query.count()

    print(f"Verification: {soil_record_count} soil records and {harvest_count} harvests remaining.")

    # Create a default farm if none exists
    farm = Farm.query.first()
    if not farm:
        print("Creating default farm...")
        farm = Farm(name="Demo Farm", location="Sample Location", size=100.0)
        db.session.add(farm)
        db.session.commit()
        print(f"Default farm created with ID: {farm.id}")
    else:
        print(f"Using existing farm: {farm.name} (ID: {farm.id})")

print("Dashboard reset complete. The dashboard is now fresh with no soil records or harvests.")
