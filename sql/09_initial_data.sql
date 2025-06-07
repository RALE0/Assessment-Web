-- Initial data for the application
-- Run after views.sql

-- Insert crops data based on label_mapping.json
INSERT INTO crops (name, description) VALUES
('rice', 'Staple grain crop grown in flooded fields'),
('maize', 'Corn - major cereal grain crop'),
('chickpea', 'Legume crop high in protein'),
('kidneybeans', 'Common bean variety rich in protein'),
('pigeonpeas', 'Drought-resistant legume crop'),
('mothbeans', 'Hardy legume adapted to arid conditions'),
('mungbean', 'Small green legume, drought tolerant'),
('blackgram', 'Black lentil, important pulse crop'),
('lentil', 'Edible pulse high in protein'),
('pomegranate', 'Fruit crop with antioxidant properties'),
('banana', 'Tropical fruit crop'),
('mango', 'Tropical stone fruit'),
('grapes', 'Vine fruit crop for fresh consumption and wine'),
('watermelon', 'Large fruit crop with high water content'),
('muskmelon', 'Sweet melon fruit crop'),
('apple', 'Temperate tree fruit crop'),
('orange', 'Citrus fruit crop'),
('papaya', 'Tropical fruit tree'),
('coconut', 'Palm tree crop for fruit and oil'),
('cotton', 'Fiber crop for textile production'),
('jute', 'Fiber crop for burlap and rope'),
('coffee', 'Beverage crop grown in tropical highlands')
ON CONFLICT (name) DO NOTHING;

-- Sample data for crop distribution colors (run once after table creation)
INSERT INTO crop_distribution_summary (crop_name, count, percentage, color, period)
VALUES 
    ('Maíz', 0, 0, '#10b981', 'current'),
    ('Frijol', 0, 0, '#059669', 'current'),
    ('Arroz', 0, 0, '#047857', 'current'),
    ('Café', 0, 0, '#065f46', 'current'),
    ('Tomate', 0, 0, '#064e3b', 'current')
ON CONFLICT (crop_name, period, calculated_at) DO NOTHING;