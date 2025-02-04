# utils.py
from datetime import datetime
from ..db import db
from ..models import BountyPoints, BugBountyWallet

def add_bounty_points(user_id, points, category, name):
    try:
        print(f"Attempting to add {points} bounty points for user {user_id} (Category: {category}, Name: {name})")
        
        # Fetch or create the user's bounty wallet
        wallet = BugBountyWallet.query.filter_by(user_id=user_id).first()
        if wallet:
            print(f"Found existing wallet for user {user_id}: Total Points = {wallet.total_points}, Recommended Points = {wallet.recommended_points}")
        else:
            print(f"No wallet found for user {user_id}. Creating a new one.")
        
        if not wallet:
            # If wallet doesn't exist, create a new wallet
            wallet = BugBountyWallet(user_id=user_id, total_points=0, recommended_points=0, month=datetime.utcnow().strftime('%m-%Y'))
            db.session.add(wallet)
            db.session.commit()  # Commit to ensure wallet has an ID
            print(f"New wallet created for user {user_id}.")

        # Add points to the wallet
        wallet.total_points += points
        wallet.recommended_points += points
        print(f"Updated wallet for user {user_id}: Total Points = {wallet.total_points}, Recommended Points = {wallet.recommended_points}")

        # Create a new BountyPoints record
        bounty_points = BountyPoints(
            wallet_id=wallet.id,
            user_id=user_id,
            name=name,
            category=category,
            points=points,
            recommended_points=points,
            last_added_points=points,
            month=datetime.utcnow().strftime('%m-%Y'),
            date=datetime.utcnow()
        )
        db.session.add(bounty_points)
        print(f"Created new BountyPoints record for user {user_id}: Points = {points}, Category = {category}")

        # Commit the changes to the database
        db.session.commit()
        print(f"Bounty points successfully added to database for user {user_id}.")

        return True  # Successfully added bounty points
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error adding bounty points for user {user_id}: {e}")
        return False  # Failed to add bounty points
