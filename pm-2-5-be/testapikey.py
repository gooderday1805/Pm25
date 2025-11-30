"""
Test timezone và crawl data thực với input ngày tự nhập
STANDALONE VERSION - Mock API để test timezone logic
"""
from datetime import datetime, timedelta
import pytz

# Timezone VN
TZ_VN = pytz.timezone('Asia/Ho_Chi_Minh')

# API Key của bạn
API_KEY = "0da082531276d74b1118047941f103c3"

# Tọa độ TP.HCM
LAT, LON = 10.8231, 106.6297


# ============================================================================
# MOCK FUNCTIONS (giống logic trong data.fetcher)
# ============================================================================

def mock_get_15_features_at_time(target_time_vn, api_key, lat, lon):
    """Mock function - giống logic thật nhưng return mock data"""
    import random
    
    # Convert to UTC (giống code thật)
    target_utc = target_time_vn.astimezone(pytz.UTC)
    timestamp_utc = int(target_utc.timestamp())
    
    print(f"\n   📡 Mock API Call:")
    print(f"      Target VN: {target_time_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"      Target UTC: {target_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"      UTC Timestamp: {timestamp_utc}")
    
    # Determine which API would be used
    now_vn = datetime.now(TZ_VN)
    target_naive = target_time_vn.replace(tzinfo=None)
    now_naive = now_vn.replace(tzinfo=None)
    
    if target_naive.date() >= now_naive.date():
        api_used = "FORECAST"
    else:
        api_used = "ARCHIVE"
    
    print(f"      API Used: {api_used}")
    
    # Return mock data với datetime giữ nguyên timezone
    return {
        "datetime": target_time_vn,  # ✅ Return với VN timezone
        # Air quality (8 features)
        "co": round(random.uniform(200, 400), 2),
        "no": round(random.uniform(0, 2), 2),
        "no2": round(random.uniform(0, 50), 2),
        "o3": round(random.uniform(50, 100), 2),
        "so2": round(random.uniform(0, 20), 2),
        "pm2_5": round(random.uniform(10, 50), 2),
        "pm10": round(random.uniform(20, 80), 2),
        "nh3": round(random.uniform(0, 10), 2),
        # Weather (7 features)
        "temperature_2m": round(random.uniform(25, 35), 2),
        "relative_humidity_2m": round(random.uniform(60, 90), 2),
        "precipitation": round(random.uniform(0, 5), 2),
        "pressure_msl": round(random.uniform(1010, 1020), 2),
        "windspeed_10m": round(random.uniform(0, 15), 2),
        "winddirection_10m": round(random.uniform(0, 360), 2),
        "shortwave_radiation": round(random.uniform(0, 800), 2),
        "_api_used": api_used  # Extra info for debugging
    }


def mock_fetch_weather_at_time(target_time_vn, lat, lon):
    """Mock fetch_weather_at_time - test API selection logic"""
    now_vn = datetime.now(TZ_VN)
    target_naive = target_time_vn.replace(tzinfo=None)
    now_naive = now_vn.replace(tzinfo=None)
    
    # ✅ ĐÚNG CODE LOGIC
    if target_naive.date() >= now_naive.date():
        api_type = "FORECAST"
        print(f"   Using FORECAST API for {target_time_vn.strftime('%Y-%m-%d %H:%M')}")
    else:
        api_type = "ARCHIVE"
        print(f"   Using ARCHIVE API for {target_time_vn.strftime('%Y-%m-%d %H:%M')}")
    
    return {"api_type": api_type}


def print_timezone_info(dt, label="Input"):
    """In chi tiết timezone info"""
    print(f"\n{'='*80}")
    print(f"🕐 {label} TIMEZONE INFO")
    print(f"{'='*80}")
    
    print(f"Raw datetime: {dt}")
    print(f"Type: {type(dt)}")
    print(f"Has timezone: {dt.tzinfo is not None}")
    
    if dt.tzinfo:
        print(f"Timezone: {dt.tzinfo}")
        print(f"UTC offset: {dt.strftime('%z')}")
        
        # Convert to different timezones
        dt_vn = dt.astimezone(TZ_VN)
        dt_utc = dt.astimezone(pytz.UTC)
        
        print(f"\n📍 Same moment in different timezones:")
        print(f"   VN Time:  {dt_vn.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
        print(f"   UTC Time: {dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print(f"⚠️  Naive datetime (no timezone)")
        print(f"   Will be treated as VN timezone")


def test_timezone_conversion():
    """Test các trường hợp timezone conversion"""
    print("\n" + "🌐"*40)
    print("TEST 1: TIMEZONE CONVERSION")
    print("🌐"*40)
    
    # Test case 1: Naive datetime
    print("\n📝 Case 1: Naive datetime (no timezone)")
    naive_dt = datetime(2024, 11, 29, 14, 30)
    print_timezone_info(naive_dt, "Naive Input")
    
    # Localize to VN
    vn_dt = TZ_VN.localize(naive_dt)
    print_timezone_info(vn_dt, "After VN localization")
    
    # Test case 2: UTC datetime
    print("\n📝 Case 2: UTC datetime")
    utc_dt = datetime(2024, 11, 29, 7, 30, tzinfo=pytz.UTC)
    print_timezone_info(utc_dt, "UTC Input")
    
    # Convert to VN
    vn_converted = utc_dt.astimezone(TZ_VN)
    print_timezone_info(vn_converted, "Converted to VN")
    
    # Verify they represent same moment
    print(f"\n✅ Verification:")
    print(f"   Naive (as VN): {vn_dt}")
    print(f"   UTC converted: {vn_converted}")
    print(f"   Are equal? {vn_dt == vn_converted}")


def test_api_selection(target_time_vn):
    """Test xem code chọn API nào (Archive vs Forecast)"""
    print("\n" + "🔀"*40)
    print("TEST 2: API SELECTION LOGIC")
    print("🔀"*40)
    
    now_vn = datetime.now(TZ_VN)
    
    print(f"\n⏰ Time comparison:")
    print(f"   Now (VN):    {now_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   Target (VN): {target_time_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # So sánh như trong code
    target_naive = target_time_vn.replace(tzinfo=None)
    now_naive = now_vn.replace(tzinfo=None)
    
    print(f"\n🔍 Date comparison (code logic):")
    print(f"   Target date: {target_naive.date()}")
    print(f"   Now date:    {now_naive.date()}")
    print(f"   target.date() >= now.date()? {target_naive.date() >= now_naive.date()}")
    
    if target_naive.date() >= now_naive.date():
        selected_api = "FORECAST"
        print(f"\n✅ Selected API: {selected_api}")
        print(f"   Reason: Target date >= today")
    else:
        selected_api = "ARCHIVE"
        print(f"\n✅ Selected API: {selected_api}")
        print(f"   Reason: Target date < today")
    
    # So sánh timestamp
    time_diff = target_time_vn - now_vn
    hours_diff = time_diff.total_seconds() / 3600
    
    print(f"\n📊 Time difference:")
    print(f"   Difference: {hours_diff:+.2f} hours ({hours_diff/24:+.2f} days)")
    
    if hours_diff > 0:
        print(f"   Status: FUTURE")
    elif hours_diff > -24:
        print(f"   Status: RECENT PAST (within 24h)")
    else:
        print(f"   Status: HISTORICAL (>{abs(hours_diff/24):.1f} days ago)")
    
    return selected_api


def test_real_api_call(target_time_str, api_key=API_KEY):
    """Test crawl data với mock API (test timezone logic)"""
    print("\n" + "🌐"*40)
    print("TEST 3: API CALL (Mock Data)")
    print("🌐"*40)
    
    # Parse input
    try:
        # Try multiple formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        
        target_dt = None
        for fmt in formats:
            try:
                target_dt = datetime.strptime(target_time_str, fmt)
                break
            except ValueError:
                continue
        
        if target_dt is None:
            raise ValueError(f"Could not parse '{target_time_str}'")
        
        print(f"\n✅ Parsed input: {target_dt}")
        
    except ValueError as e:
        print(f"❌ Invalid time format: {e}")
        return None
    
    # Localize to VN timezone
    target_vn = TZ_VN.localize(target_dt)
    print(f"🇻🇳 VN Time: {target_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Convert to UTC
    target_utc = target_vn.astimezone(pytz.UTC)
    print(f"🌍 UTC Time: {target_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Test API selection
    selected_api = test_api_selection(target_vn)
    
    # Call mock API
    print(f"\n🚀 Calling API (Mock)...")
    print(f"   API Key: {'*'*20}{api_key[-4:]}")
    print(f"   Location: ({LAT}, {LON}) - TP.HCM")
    print(f"   Target: {target_vn}")
    
    try:
        # Get 15 features (mock)
        result = mock_get_15_features_at_time(target_vn, api_key, LAT, LON)
        
        print(f"\n✅ API CALL SUCCESSFUL!")
        
        # Display results
        print(f"\n{'='*80}")
        print(f"📊 CRAWLED DATA RESULTS (Mock)")
        print(f"{'='*80}")
        
        print(f"\n🕐 Datetime (returned):")
        print(f"   {result['datetime']}")
        print(f"   Timezone: {result['datetime'].tzinfo}")
        
        print(f"\n🏭 AIR QUALITY DATA (8 features):")
        air_features = ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
        for feat in air_features:
            if feat in result:
                print(f"   {feat:8s}: {result[feat]:10.2f} μg/m³")
        
        print(f"\n☀️  WEATHER DATA (7 features):")
        weather_features = [
            'temperature_2m', 'relative_humidity_2m', 'precipitation',
            'pressure_msl', 'windspeed_10m', 'winddirection_10m',
            'shortwave_radiation'
        ]
        for feat in weather_features:
            if feat in result:
                unit = get_unit(feat)
                print(f"   {feat:25s}: {result[feat]:8.2f} {unit}")
        
        # Verify datetime timezone
        print(f"\n✅ TIMEZONE VERIFICATION:")
        returned_dt = result['datetime']
        print(f"   Input timezone:    {target_vn.tzinfo}")
        print(f"   Returned timezone: {returned_dt.tzinfo}")
        print(f"   Is VN timezone?    {returned_dt.tzinfo == TZ_VN}")
        print(f"   Matches input?     {returned_dt == target_vn}")
        print(f"   API used:          {result['_api_used']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ API CALL FAILED!")
        print(f"   Error: {str(e)}")
        
        import traceback
        print(f"\n📋 Full traceback:")
        traceback.print_exc()
        
        return None


def get_unit(feature_name):
    """Get unit for each feature"""
    units = {
        'co': 'μg/m³',
        'no': 'μg/m³',
        'no2': 'μg/m³',
        'o3': 'μg/m³',
        'so2': 'μg/m³',
        'pm2_5': 'μg/m³',
        'pm10': 'μg/m³',
        'nh3': 'μg/m³',
        'temperature_2m': '°C',
        'relative_humidity_2m': '%',
        'precipitation': 'mm',
        'pressure_msl': 'hPa',
        'windspeed_10m': 'm/s',
        'winddirection_10m': '°',
        'shortwave_radiation': 'W/m²'
    }
    return units.get(feature_name, '')


def interactive_test():
    """Interactive mode để nhập thời gian"""
    print("\n" + "🎮"*40)
    print("INTERACTIVE TEST MODE")
    print("🎮"*40)
    
    print("\n📝 Nhập thời gian cần test (format: YYYY-MM-DD HH:MM)")
    print("   Ví dụ: 2024-11-29 14:30")
    print("   Hoặc: 2024-11-29 5:00")
    print("   Hoặc để trống để dùng ví dụ mặc định")
    
    user_input = input("\n⌨️  Nhập thời gian: ").strip()
    
    if not user_input:
        # Default examples
        examples = [
            ("Hôm qua 14:30", (datetime.now(TZ_VN) - timedelta(days=1)).replace(hour=14, minute=30, second=0, microsecond=0)),
            ("Hôm nay 10:00", datetime.now(TZ_VN).replace(hour=10, minute=0, second=0, microsecond=0)),
            ("Ngày mai 15:00", (datetime.now(TZ_VN) + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)),
        ]
        
        print("\n📋 Chọn ví dụ:")
        for i, (name, dt) in enumerate(examples, 1):
            print(f"   {i}. {name}: {dt.strftime('%Y-%m-%d %H:%M')}")
        
        choice = input("\n⌨️  Chọn (1-3): ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                target_time_str = examples[idx][1].strftime('%Y-%m-%d %H:%M')
            else:
                print("❌ Invalid choice, using default")
                target_time_str = examples[0][1].strftime('%Y-%m-%d %H:%M')
        except:
            print("❌ Invalid choice, using default")
            target_time_str = examples[0][1].strftime('%Y-%m-%d %H:%M')
    else:
        target_time_str = user_input
    
    print(f"\n🎯 Testing with: {target_time_str}")
    
    # Run tests
    test_timezone_conversion()
    result = test_real_api_call(target_time_str)
    
    return result


def main():
    """Main function"""
    print("\n" + "="*80)
    print("🧪 TEST TIMEZONE & REAL API CRAWL")
    print("="*80)
    
    print("\nOptions:")
    print("  1. Interactive test (nhập thời gian)")
    print("  2. Quick test với thời gian cụ thể")
    print("  3. Test timezone conversion only")
    
    choice = input("\nChọn option (1-3): ").strip()
    
    if choice == "1":
        interactive_test()
    
    elif choice == "2":
        # Quick test
        test_times = [
            "2024-11-29 14:30",
            "2024-11-30 10:00",
            "2024-12-01 15:00",
        ]
        
        print("\n📋 Quick test với 3 thời gian:")
        for i, time_str in enumerate(test_times, 1):
            print(f"\n{'='*80}")
            print(f"Test {i}/3: {time_str}")
            print(f"{'='*80}")
            test_real_api_call(time_str)
    
    elif choice == "3":
        test_timezone_conversion()
    
    else:
        print("❌ Invalid choice")
        return
    
    print("\n" + "="*80)
    print("🎉 TESTS COMPLETED!")
    print("="*80)


if __name__ == "__main__":
    main()