# Product Overview

## Project Purpose
FoodWaste is a Django web application that connects food donors with receivers and NGOs to reduce food waste. It enables donors to list surplus food, receivers to request it, and NGOs to coordinate and manage deliveries.

## Value Proposition
- Reduces food waste by redistributing surplus food to those in need
- Provides a structured workflow: donation → request → NGO-managed delivery
- Supports role-based access so each user type sees a tailored experience

## Key Features
- **Food Listings**: Donors post food items with name, description, quantity, preparation/expiry times, location, and optional image
- **Food Requests**: Receivers browse available food and submit requests with optional messages
- **Delivery Management**: NGOs accept delivery assignments and track status through a multi-step pipeline (pending → accepted → taken → received → delivered)
- **Role-Based Dashboards**: Separate dashboards for donors, receivers, and NGOs
- **User Accounts**: Custom user model with roles (donor, receiver, ngo), phone, and address fields
- **Password Reset**: Multi-step password reset via email or phone contact choice
- **Expired Food Cleanup**: Management command (`delete_expired_food`) to remove expired listings automatically
- **Media Uploads**: Food images stored under `media/food_images/`

## Target Users
| Role | Responsibilities |
|------|-----------------|
| Donor | Lists surplus food, reviews incoming requests, accepts/rejects them |
| Receiver | Browses available food, submits requests, tracks delivery status |
| NGO | Views accepted requests, manages and updates delivery logistics |

## Use Cases
1. A restaurant has leftover food at end of day → donor posts listing → receiver requests it → NGO picks up and delivers
2. An individual wants to donate home-cooked food → posts with expiry time → system auto-cleans expired posts
3. An NGO coordinates multiple deliveries across the city using the NGO dashboard
