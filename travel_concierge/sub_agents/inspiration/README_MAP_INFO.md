# Hướng Dẫn Sử Dụng map_url và place_id trong Inspiration Agent

## Tổng Quan

Inspiration Agent hiện tại đã được cập nhật để hiển thị thông tin `map_url` và `place_id` trong response khi gợi ý Points of Interest (POI). Những thông tin này cung cấp khả năng điều hướng trực tiếp và tích hợp với Google Maps.

## Cấu Trúc Response

### POI Response Format

Khi gọi `poi_agent`, response sẽ bao gồm:

```json
{
  "places": [
    {
      "place_name": "Tên điểm tham quan",
      "address": "Địa chỉ đầy đủ",
      "lat": "Vĩ độ",
      "long": "Kinh độ",
      "review_ratings": "Đánh giá số",
      "highlights": "Mô tả đặc điểm nổi bật",
      "image_url": "URL hình ảnh",
      "map_url": "URL Google Maps",
      "place_id": "Google Place ID"
    }
  ]
}
```

### Ví Dụ Thực Tế

```json
{
  "places": [
    {
      "place_name": "Eiffel Tower",
      "address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France",
      "lat": "48.8584",
      "long": "2.2945",
      "review_ratings": "4.6",
      "highlights": "Iconic iron lattice tower and symbol of Paris with panoramic city views",
      "image_url": "https://example.com/eiffel-tower.jpg",
      "map_url": "https://www.google.com/maps/place/?q=place_id:ChIJLU7jZClu5kcR4PcOOO6p3I0",
      "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0"
    }
  ]
}
```

## Quy Trình Xử Lý

### 1. Khởi Tạo Ban Đầu
- `poi_agent` tạo POI suggestions với `map_url` và `place_id` = `""`
- Cung cấp thông tin cơ bản: tên, địa chỉ, tọa độ ước tính

### 2. Xử Lý bởi map_tool
- Inspiration agent tự động gọi `map_tool` sau `poi_agent`
- `map_tool` sử dụng Google Places API để:
  - Xác minh và cập nhật tọa độ chính xác
  - Tạo `map_url` theo format: `https://www.google.com/maps/place/?q=place_id:{place_id}`
  - Lấy `place_id` từ Google Places API

### 3. Response Cuối Cùng
- User nhận được POI với đầy đủ thông tin navigation
- Có thể click `map_url` để mở trực tiếp trong Google Maps
- Có thể sử dụng `place_id` cho các API calls khác

## Cách Sử Dụng

### Cho User Interface
```javascript
// Hiển thị link điều hướng
<a href={poi.map_url} target="_blank">
  📍 Xem trên Google Maps
</a>

// Hoặc sử dụng place_id cho custom maps
const customMapUrl = `https://www.google.com/maps/embed/v1/place?key=${API_KEY}&q=place_id:${poi.place_id}`;
```

### Cho API Integration
```python
# Sử dụng place_id cho Google Places API
place_details = places_client.place(
    place_id=poi.place_id,
    fields=['photos', 'reviews', 'opening_hours']
)
```

## Lợi Ích

1. **Navigation Trực Tiếp**: Users có thể click để mở Google Maps ngay lập tức
2. **Tích Hợp Dễ Dàng**: place_id có thể được sử dụng với các Google APIs khác
3. **Thông Tin Chính Xác**: Tọa độ và thông tin được xác minh bởi Google Places API
4. **User Experience Tốt**: Giảm friction khi users muốn tìm hiểu thêm về địa điểm

## Cập Nhật Gần Đây

- ✅ Cập nhật prompt instructions để hiển thị rõ ràng về map_url và place_id
- ✅ Thêm example output format trong POI_AGENT_INSTR
- ✅ Cải thiện field descriptions trong types.py
- ✅ Đảm bảo inspiration agent luôn gọi map_tool sau poi_agent

## Debug và Troubleshooting

### Kiểm Tra map_url và place_id Có Được Populate
```python
# Log để kiểm tra
print(f"map_url: {poi.map_url}")
print(f"place_id: {poi.place_id}")
```

### Nếu Fields Vẫn Empty
1. Đảm bảo GOOGLE_PLACES_API_KEY được set trong environment
2. Kiểm tra map_tool có được gọi sau poi_agent không
3. Verify address information đủ chi tiết để geocoding

## Environment Setup

Đảm bảo có API key:
```bash
export GOOGLE_PLACES_API_KEY="your-google-places-api-key"
```