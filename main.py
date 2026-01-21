from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db import create_tables
from routes.auth import admin_routes, student_routes, teacher_routes, counsellor_routes
from routes.courses import course_routes
from routes.classroom import classroom_routes
from routes.aboutus import about_us_routes
from routes.help_center import help_center_routes
from routes.admission import admission_code_routes
from routes.admission import admission_enquiry_routes
from routes.ads import ads_routes
from routes.announcement import announcement_routes
# Create FastAPI app
app = FastAPI(
    title="VWINGS24X7 Backend API",
    description="Backend API for Admin Management",
    version="1.0.0"
)

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount /uploads as static files so course videos/photos can be accessed via URL
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify server status
    """
    return {
        "status": "healthy",
        "message": "Server is running successfully"
    }

# Register routers
app.include_router(admin_routes.router)
app.include_router(course_routes.router)
app.include_router(classroom_routes.router)
app.include_router(about_us_routes.router)
app.include_router(help_center_routes.router)
app.include_router(student_routes.router)
app.include_router(teacher_routes.router)
app.include_router(counsellor_routes.router)
app.include_router(admission_code_routes.router)
app.include_router(admission_enquiry_routes.router)
app.include_router(ads_routes.router)
app.include_router(announcement_routes.router)

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")

# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to VWINGS24X7 Backend API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    # Run on all IPs (0.0.0.0) to ensure accessibility
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
