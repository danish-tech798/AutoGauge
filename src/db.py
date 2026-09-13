"""
db.py - Database Module
-----------------------
Handles all SQLite database operations for AutoGauge:
- User registration & login
- User profile management
- Estimation history storage
- Saved vehicles
"""

import sqlite3
import os
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "autogauge.db")


class AutoGaugeDB:
    """SQLite database handler for AutoGauge."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Estimations table (history of price predictions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estimations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                brand TEXT,
                model TEXT,
                year INTEGER,
                km_driven INTEGER,
                fuel_type TEXT,
                transmission TEXT,
                city TEXT,
                body_type TEXT,
                owner_count INTEGER,
                condition TEXT,
                predicted_price REAL,
                condition_score REAL,
                damage_detected TEXT,
                base_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Saved vehicles table (favorites)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                estimation_id INTEGER,
                vehicle_name TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (estimation_id) REFERENCES estimations(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def signup(self, email: str, password: str, full_name: str = "", phone: str = "") -> Tuple[bool, str]:
        """
        Register a new user.
        Returns: (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, phone)
                VALUES (?, ?, ?, ?)
            """, (email, password_hash, full_name, phone))
            
            conn.commit()
            conn.close()
            
            return True, "Signup successful! Please login."
        
        except sqlite3.IntegrityError:
            return False, "Email already registered. Please login or use a different email."
        except Exception as e:
            return False, f"Signup error: {str(e)}"
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user.
        Returns: (success: bool, user_data: dict or None)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            
            cursor.execute("""
                SELECT id, email, full_name, phone, created_at FROM users
                WHERE email = ? AND password_hash = ?
            """, (email, password_hash))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return True, dict(user)
            else:
                return False, None
        
        except Exception as e:
            return False, None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user profile by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, full_name, phone, created_at FROM users
                WHERE id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            return dict(user) if user else None
        except Exception as e:
            return None
    
    def update_user_profile(self, user_id: int, full_name: str = "", phone: str = "") -> Tuple[bool, str]:
        """Update user profile information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (full_name, phone, user_id))
            
            conn.commit()
            conn.close()
            
            return True, "Profile updated successfully!"
        except Exception as e:
            return False, f"Update error: {str(e)}"
    
    def save_estimation(self, user_id: int, estimation_data: Dict) -> Tuple[bool, int]:
        """
        Save an estimation/prediction to history.
        Returns: (success: bool, estimation_id: int)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO estimations (
                    user_id, brand, model, year, km_driven, fuel_type,
                    transmission, city, body_type, owner_count, condition,
                    predicted_price, condition_score, damage_detected, base_price
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                estimation_data.get("brand"),
                estimation_data.get("model"),
                estimation_data.get("year"),
                estimation_data.get("km_driven"),
                estimation_data.get("fuel_type"),
                estimation_data.get("transmission"),
                estimation_data.get("city"),
                estimation_data.get("body_type"),
                estimation_data.get("owner_count"),
                estimation_data.get("condition"),
                estimation_data.get("predicted_price"),
                estimation_data.get("condition_score"),
                json.dumps(estimation_data.get("damage_detected", [])),
                estimation_data.get("base_price"),
            ))
            
            estimation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True, estimation_id
        except Exception as e:
            return False, -1
    
    def get_estimation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's estimation history."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM estimations
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            estimations = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Parse JSON damage_detected field
            for est in estimations:
                if est.get("damage_detected"):
                    try:
                        est["damage_detected"] = json.loads(est["damage_detected"])
                    except:
                        est["damage_detected"] = []
            
            return estimations
        except Exception as e:
            return []
    
    def get_estimation_count(self, user_id: int) -> int:
        """Get total number of estimations for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM estimations
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
        except Exception as e:
            return 0
    
    def save_vehicle(self, user_id: int, estimation_id: int, vehicle_name: str, notes: str = "") -> Tuple[bool, str]:
        """Save/favorite a vehicle."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO saved_vehicles (user_id, estimation_id, vehicle_name, notes)
                VALUES (?, ?, ?, ?)
            """, (user_id, estimation_id, vehicle_name, notes))
            
            conn.commit()
            conn.close()
            
            return True, "Vehicle saved!"
        except Exception as e:
            return False, f"Save error: {str(e)}"
    
    def get_saved_vehicles(self, user_id: int) -> List[Dict]:
        """Get user's saved vehicles."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sv.*, e.* FROM saved_vehicles sv
                LEFT JOIN estimations e ON sv.estimation_id = e.id
                WHERE sv.user_id = ?
                ORDER BY sv.created_at DESC
            """, (user_id,))
            
            vehicles = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return vehicles
        except Exception as e:
            return []
    
    def delete_estimation(self, estimation_id: int, user_id: int) -> Tuple[bool, str]:
        """Delete an estimation (with authorization check)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check ownership
            cursor.execute("SELECT user_id FROM estimations WHERE id = ?", (estimation_id,))
            result = cursor.fetchone()
            
            if not result or result[0] != user_id:
                return False, "Unauthorized"
            
            cursor.execute("DELETE FROM estimations WHERE id = ?", (estimation_id,))
            conn.commit()
            conn.close()
            
            return True, "Estimation deleted"
        except Exception as e:
            return False, f"Delete error: {str(e)}"
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            old_hash = self._hash_password(old_password)
            new_hash = self._hash_password(new_password)
            
            cursor.execute("""
                SELECT id FROM users 
                WHERE id = ? AND password_hash = ?
            """, (user_id, old_hash))
            
            if not cursor.fetchone():
                return False, "Current password is incorrect"
            
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_hash, user_id))
            
            conn.commit()
            conn.close()
            
            return True, "Password changed successfully!"
        except Exception as e:
            return False, f"Error: {str(e)}"


# Initialize database
db = AutoGaugeDB()
