# 🔳 **QR Rectangle Constructor - Feature Documentation**

## 📖 **Overview**

The QR Rectangle Constructor connects the three detected QR finder pattern centers to form complete rectangles by calculating the missing fourth corner. This provides a complete boundary visualization of the QR code area.

## 🎯 **Key Features**

### **Automatic Fourth Corner Calculation**

- Uses parallelogram rule: `D = A + C - B` where A, B, C are known corners
- Verification using vector methods for consistency checking
- High accuracy with minimal discrepancy

### **Complete Rectangle Properties**

- **Corner coordinates** for all four positions
- **Side lengths** for all edges
- **Diagonal measurements**
- **Area calculation** in square pixels
- **Angle measurements** at each corner
- **Aspect ratio** analysis

### **Validation System**

- **Rectangle validity** checking (angles close to 90°)
- **Parallel sides** verification
- **Geometric consistency** validation
- **Calculation method** verification

## 🚀 **Usage**

### **Run Rectangle Construction**

```bash
python3 qr_rectangle_constructor.py
```

### **View Results Summary**

```bash
python3 view_rectangles.py
```

## 📁 **Output Files**

### **For Each Image**

- **`{image_name}_rectangle.png`** - Visual representation with:

  - ✅ Original finder patterns (positions 1, 2, 3)
  - 🆕 Calculated fourth corner (position 4)
  - 🔳 Complete rectangle outline
  - 📐 Diagonal lines
  - 📊 Properties overlay

- **`{image_name}_rectangle.json`** - Complete data including:
  - Corner coordinates for all four positions
  - Rectangle properties (area, sides, angles)
  - Calculation verification data
  - Original pattern information

### **Combined Results**

- **`all_rectangles.json`** - All rectangle data in one file

## 🎯 **Results Summary**

From the current test images:

| Image         | Valid Rectangle | Area (px²) | Aspect Ratio | Angle Range |
| ------------- | --------------- | ---------- | ------------ | ----------- |
| image copy 3  | ❌ No           | 6,834      | 1.012        | 77.4°       |
| image copy 11 | ✅ Yes          | 13,715     | 1.134        | 85.7°       |
| image         | ✅ Yes          | 40,239     | 0.832        | 80.8°       |

**Success Rate**: 66.7% (2/3 valid rectangles)

## 🔍 **Technical Details**

### **Corner Positions**

```
2️⃣ Left Top ────────── 3️⃣ Right Top
│                             │
│          QR CODE            │
│                             │
1️⃣ Left Bottom ─────── 4️⃣ Right Bottom
                      [Calculated]
```

### **Calculation Method**

The fourth corner is calculated using the **parallelogram rule**:

- Given three corners A (pos1), B (pos2), C (pos3)
- Calculate D (pos4) = A + C - B
- This ensures ABCD forms a proper parallelogram

### **Validation Criteria**

- **Angles**: Each corner should be close to 90° (tolerance: 80°-100°)
- **Parallel sides**: Opposite sides should be approximately equal
- **Consistency**: Vector and parallelogram methods should agree

## 📊 **Example Output**

```
📷 image copy 11
📍 Corner Coordinates:
   1️⃣ Left Bottom:   (105, 254)
   2️⃣ Left Top:      (100, 144)
   3️⃣ Right Top:     (224, 129)
   4️⃣ Right Bottom:  (229, 239) [Calculated]

📐 Rectangle Properties:
   📏 Dimensions: 110.1 × 124.9 px
   📊 Area: 13,715 px²
   📐 Aspect Ratio: 1.134
   ✅ Valid Rectangle: True
   📐 Angle Range: 85.7° - 85.7°
```

## 🎨 **Visualization Features**

- **Color-coded corners**: Different colors for each position
- **Rectangle outline**: Clear boundary visualization
- **Diagonal lines**: Show geometric relationships
- **Properties overlay**: Key measurements displayed
- **Position labels**: Clear numbering and naming

## 🔧 **Integration**

The rectangle constructor integrates seamlessly with:

- **QR finder pattern detection** (provides input data)
- **Position numbering system** (uses numbered positions)
- **Orientation analysis** (rectangle can enhance orientation detection)
- **Result visualization** (adds geometric context)

## 🎯 **Applications**

1. **QR Code Boundary Detection** - Complete area visualization
2. **Geometric Analysis** - Shape and proportion measurement
3. **Orientation Enhancement** - Rectangle aids rotation detection
4. **Quality Assessment** - Validate QR code geometry
5. **Template Generation** - Create design guidelines

---

_This feature completes the QR detection pipeline by providing full geometric reconstruction from finder patterns._
