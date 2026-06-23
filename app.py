from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret Key
app.secret_key = os.getenv("SECRET_KEY", "smartlogistics")
import os
import mysql.connector

db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST", "reseau.proxy.rlwy.net"),
    user=os.getenv("MYSQLUSER", "root"),
    password=os.getenv("MYSQLPASSWORD", "AngmmmSjXojoJBFKkoByNZURFGKCQGhy"),
    database=os.getenv("MYSQLDATABASE", "railway"),
    port=int(os.getenv("MYSQLPORT", "38885"))
)

cursor = db.cursor(dictionary=True)


# HOME PAGE
@app.route("/")
def home():

    return render_template(
        "index.html",
        shipment=None,
        error=None
    )
@app.route("/track", methods=["POST"])
def track():

    tracking_id = request.form["tracking_id"]

    cursor.execute(
        """
        SELECT *
        FROM shipments
        WHERE tracking_id=%s
        """,
        (tracking_id.strip(),)
    )

    shipment = cursor.fetchone()

    if shipment:

        return render_template(
            "index.html",
            shipment=shipment,
            error=None
        )

    return render_template(
        "index.html",
        shipment=None,
        error="Tracking ID not found"
    )
# LOGIN PAGE

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=%s
            """,
            (username,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user"] = user["username"]
            session["role"] = user["role"]

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        role = request.form["role"]

        password = generate_password_hash(
            request.form["password"]
        )

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=%s
            """,
            (username,)
        )

        existing = cursor.fetchone()

        if existing:

            return render_template(
                "register.html",
                error="Username already exists"
            )

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password,
                role
            )
            VALUES
            (%s,%s,%s,%s)
            """,
            (
                username,
                email,
                password,
                role
            )
        )

        db.commit()

        return redirect("/login")

    return render_template("register.html")

# LOGOUT

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# DASHBOARD

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    # Total Shipments
    cursor.execute(
        "SELECT COUNT(*) AS total FROM shipments"
    )
    total = cursor.fetchone()["total"]

    # Delivered
    cursor.execute("""
        SELECT COUNT(*) AS delivered
        FROM shipments
        WHERE status='Delivered'
    """)
    delivered = cursor.fetchone()["delivered"]

    # In Transit
    cursor.execute("""
        SELECT COUNT(*) AS transit
        FROM shipments
        WHERE status='In Transit'
    """)
    transit = cursor.fetchone()["transit"]

    # Pending
    cursor.execute("""
        SELECT COUNT(*) AS pending
        FROM shipments
        WHERE status='Pending'
    """)
    pending = cursor.fetchone()["pending"]

    # Recent Shipments
    cursor.execute("""
        SELECT
            tracking_id,
            destination,
            status
        FROM shipments
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_shipments = cursor.fetchall()

    # Top Warehouses
    cursor.execute("""
        SELECT
            warehouse_name,
            capacity_used
        FROM warehouses
        ORDER BY capacity_used DESC
        LIMIT 3
    """)
    top_warehouses = cursor.fetchall()

    # Latest Notifications
    cursor.execute("""
        SELECT *
        FROM notifications
        ORDER BY created_at DESC
        LIMIT 5
    """)
    notifications = cursor.fetchall()

    return render_template(
        "dashboard.html",
        total=total,
        delivered=delivered,
        transit=transit,
        pending=pending,
        recent_shipments=recent_shipments,
        top_warehouses=top_warehouses,
        notifications=notifications
    )
@app.route("/shipments")
def shipments():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search")

    if search:

        cursor.execute(
            """
            SELECT *
            FROM shipments
            WHERE tracking_id LIKE %s
            """,
            ("%" + search + "%",)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM shipments
            """
        )

    shipment_data = cursor.fetchall()

    return render_template(
        "shipments.html",
        shipments=shipment_data
    )
@app.route("/add_shipment", methods=["POST"])
def add_shipment():

    if "user" not in session:

        return redirect("/login")

    tracking_id = request.form["tracking_id"]
    origin = request.form["origin"]
    destination = request.form["destination"]
    status = request.form["status"]
    current_location = request.form["current_location"]

    query = """
    INSERT INTO shipments
    (
        tracking_id,
        origin,
        destination,
        status,
        current_location
    )
    VALUES
    (%s,%s,%s,%s,%s)
    """

    cursor.execute(
        query,
        (
            tracking_id,
            origin,
            destination,
            status,
            current_location
        )
    )
    cursor.execute(
    """
    INSERT INTO notifications(message)
    VALUES(%s)
    """,
    (
        f"New shipment {tracking_id} added",
    )
)

    db.commit()

    return redirect("/shipments")
@app.route("/delete_shipment/<int:id>")
def delete_shipment(id):

    if "user" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT tracking_id FROM shipments WHERE id=%s",
        (id,)
    )

    shipment = cursor.fetchone()

    if shipment:

        cursor.execute(
            """
            INSERT INTO notifications(message)
            VALUES(%s)
            """,
            (
                f"Shipment {shipment['tracking_id']} deleted",
            )
        )

    cursor.execute(
        """
        DELETE FROM shipments
        WHERE id=%s
        """,
        (id,)
    )

    db.commit()

    return redirect("/shipments")
@app.route("/edit_shipment/<int:id>")
def edit_shipment(id):

    if "user" not in session:
        return redirect("/login")

    cursor.execute(
        """
        SELECT *
        FROM shipments
        WHERE id=%s
        """,
        (id,)
    )

    shipment = cursor.fetchone()

    return render_template(
        "edit_shipment.html",
        shipment=shipment
    )


@app.route("/update_shipment/<int:id>", methods=["POST"])
def update_shipment(id):

    if "user" not in session:
        return redirect("/login")

    tracking_id = request.form["tracking_id"]
    origin = request.form["origin"]
    destination = request.form["destination"]
    status = request.form["status"]
    current_location = request.form["current_location"]

    cursor.execute(
        """
        UPDATE shipments
        SET
        tracking_id=%s,
        origin=%s,
        destination=%s,
        status=%s,
        current_location=%s
        WHERE id=%s
        """,
        (
            tracking_id,
            origin,
            destination,
            status,
            current_location,
            id
        )
    )

    db.commit()

    return redirect("/shipments")

# ANALYTICS

@app.route("/analytics")
def analytics():

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        "SELECT COUNT(*) AS total FROM shipments"
    )
    total_shipments = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS delivered
        FROM shipments
        WHERE status='Delivered'
        """
    )
    delivered = cursor.fetchone()["delivered"]

    cursor.execute(
        """
        SELECT COUNT(*) AS transit
        FROM shipments
        WHERE status='In Transit'
        """
    )
    transit = cursor.fetchone()["transit"]

    cursor.execute(
        """
        SELECT COUNT(*) AS pending
        FROM shipments
        WHERE status='Pending'
        """
    )
    pending = cursor.fetchone()["pending"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM warehouses"
    )
    total_warehouses = cursor.fetchone()["total"]
    cursor.execute("""
SELECT warehouse_name, capacity_used
FROM warehouses
""")

    warehouse_data = cursor.fetchall()

    return render_template(
        "analytics.html",
        total_shipments=total_shipments,
        delivered=delivered,
        transit=transit,
        pending=pending,
        total_warehouses=total_warehouses,
        warehouses=warehouse_data
    )
# WAREHOUSE

@app.route("/warehouse")
def warehouse():

    search = request.args.get("search")

    if search:

        cursor.execute(
            """
            SELECT *
            FROM warehouses
            WHERE warehouse_name LIKE %s
            OR location LIKE %s
            """,
            (
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM warehouses
            """
        )

    warehouse_data = cursor.fetchall()

    return render_template(
        "warehouse.html",
        warehouses=warehouse_data
    )
@app.route("/add_warehouse", methods=["POST"])
def add_warehouse():

    if "user" not in session:

        return redirect("/login")

    warehouse_name = request.form["warehouse_name"]
    location = request.form["location"]
    capacity_used = request.form["capacity_used"]

    cursor.execute(
        """
        INSERT INTO warehouses
        (
            warehouse_name,
            location,
            capacity_used
        )
        VALUES
        (%s,%s,%s)
        """,
        (
            warehouse_name,
            location,
            capacity_used
        )
    )
    cursor.execute(
    """
    INSERT INTO notifications(message)
    VALUES(%s)
    """,
    (
        f"New warehouse {warehouse_name} added",
    )
)

    db.commit()

    return redirect("/warehouse")
@app.route("/delete_warehouse/<int:id>")
def delete_warehouse(id):

    if "user" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT warehouse_name FROM warehouses WHERE id=%s",
        (id,)
    )

    warehouse = cursor.fetchone()

    if warehouse:

        cursor.execute(
            """
            INSERT INTO notifications(message)
            VALUES(%s)
            """,
            (
                f"Warehouse {warehouse['warehouse_name']} deleted",
            )
        )

    cursor.execute(
        """
        DELETE FROM warehouses
        WHERE id=%s
        """,
        (id,)
    )

    db.commit()

    return redirect("/warehouse")
@app.route("/edit_warehouse/<int:id>")
def edit_warehouse(id):

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        """
        SELECT *
        FROM warehouses
        WHERE id=%s
        """,
        (id,)
    )

    warehouse = cursor.fetchone()

    return render_template(
        "edit_warehouse.html",
        warehouse=warehouse
    )
@app.route("/update_warehouse/<int:id>",
methods=["POST"])
def update_warehouse(id):

    if "user" not in session:

        return redirect("/login")

    warehouse_name = request.form["warehouse_name"]
    location = request.form["location"]
    capacity_used = request.form["capacity_used"]

    cursor.execute(
        """
        UPDATE warehouses
        SET
        warehouse_name=%s,
        location=%s,
        capacity_used=%s
        WHERE id=%s
        """,
        (
            warehouse_name,
            location,
            capacity_used,
            id
        )
    )

    db.commit()

    return redirect("/warehouse")



# SETTINGS

@app.route('/settings')
def settings():

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        "SELECT * FROM settings WHERE id=1"
    )

    settings_data = cursor.fetchone()

    return render_template(
        "settings.html",
        settings=settings_data
    )


@app.route('/update_settings', methods=['POST'])
def update_settings():

    if "user" not in session:

        return redirect("/login")

    company_name = request.form["company_name"]
    admin_email = request.form["admin_email"]
    contact_number = request.form["contact_number"]

    cursor.execute(
        """
        UPDATE settings
        SET
        company_name=%s,
        admin_email=%s,
        contact_number=%s
        WHERE id=1
        """,
        (
            company_name,
            admin_email,
            contact_number
        )
    )

    db.commit()

    return redirect('/settings')
@app.route(
    "/update_notifications",
    methods=["POST"]
)
def update_notifications():

    if "user" not in session:

        return redirect("/login")

    email_alerts = 1 if \
        request.form.get(
            "email_alerts"
        ) else 0

    shipment_notifications = 1 if \
        request.form.get(
            "shipment_notifications"
        ) else 0

    cursor.execute(
        """
        UPDATE settings
        SET
        email_alerts=%s,
        shipment_notifications=%s
        WHERE id=1
        """,
        (
            email_alerts,
            shipment_notifications
        )
    )

    db.commit()

    return redirect("/settings")
@app.route(
    "/update_password",
    methods=["POST"]
)
def update_password():

    if "user" not in session:

        return redirect("/login")

    current_password = request.form[
        "current_password"
    ]

    new_password = request.form[
        "new_password"
    ]

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username=%s
        """,
        (session["user"],)
    )

    user = cursor.fetchone()

    if user and check_password_hash(
        user["password"],
        current_password
    ):

        hashed_password = generate_password_hash(
            new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password=%s
            WHERE username=%s
            """,
            (
                hashed_password,
                session["user"]
            )
        )

        db.commit()

    return redirect("/settings")
# USERS

@app.route("/users")
def users():

    search = request.args.get("search")

    if search:

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username LIKE %s
            OR email LIKE %s
            OR role LIKE %s
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM users
            """
        )

    users = cursor.fetchall()

    admin_count = len(
        [u for u in users if u["role"] == "Administrator"]
    )

    manager_count = len(
        [u for u in users if u["role"] == "Manager"]
    )

    warehouse_count = len(
        [u for u in users if u["role"] == "Warehouse Staff"]
    )

    return render_template(
        "users.html",
        users=users,
        admin_count=admin_count,
        manager_count=manager_count,
        warehouse_count=warehouse_count
    )
       


@app.route("/add_user", methods=["POST"])
def add_user():

    if "user" not in session:

        return redirect("/login")

    username = request.form["username"]
    email = request.form["email"]

    password = generate_password_hash(
        request.form["password"]
    )

    role = request.form["role"]

    cursor.execute(
        """
        INSERT INTO users
        (
            username,
            email,
            password,
            role
        )
        VALUES
        (%s,%s,%s,%s)
        """,
        (
            username,
            email,
            password,
            role
        )
    )

    cursor.execute(
        """
        INSERT INTO notifications(message)
        VALUES(%s)
        """,
        (
            f"New user {username} created",
        )
    )

    db.commit()

    return redirect("/users")


@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        """
        DELETE FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    db.commit()

    return redirect("/users")
@app.route("/edit_user/<int:user_id>")
def edit_user(user_id):

    if "user" not in session:

        return redirect("/login")

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    return render_template(
        "edit_user.html",
        user=user
    )
@app.route(
    "/update_user/<int:user_id>",
    methods=["POST"]
)
def update_user(user_id):

    if "user" not in session:

        return redirect("/login")

    username = request.form["username"]
    email = request.form["email"]
    role = request.form["role"]

    cursor.execute(
        """
        UPDATE users
        SET
        username=%s,
        email=%s,
        role=%s
        WHERE id=%s
        """,
        (
            username,
            email,
            role,
            user_id
        )
    )

    db.commit()

    return redirect("/users")
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT COUNT(*) AS total FROM shipments"
    )

    shipments = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM warehouses"
    )

    warehouses = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM users"
    )

    users = cursor.fetchone()["total"]

    return render_template(
        "profile.html",
        shipments=shipments,
        warehouses=warehouses,
        users=users
    )
@app.route("/upgrade")
def upgrade():

    if "user" not in session:
        return redirect("/login")

    return render_template("upgrade.html")
@app.route("/help")
def help():

    if "user" not in session:
        return redirect("/login")

    cursor.execute("SELECT COUNT(*) AS total FROM shipments")
    shipments = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM warehouses")
    warehouses = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    users = cursor.fetchone()["total"]

    return render_template(
        "help.html",
        shipments=shipments,
        warehouses=warehouses,
        users=users
    )
@app.route("/contact", methods=["POST"])
def contact():

    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    cursor.execute(
        """
        INSERT INTO contact_messages
        (name, email, message)
        VALUES (%s,%s,%s)
        """,
        (name, email, message)
    )

    db.commit()

    flash("✅ Message sent successfully! We will contact you soon.")

    return redirect("/#contact")
if __name__ == "__main__":

    app.run(debug=True)