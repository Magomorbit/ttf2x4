#!/usr/bin/env python3
"""
Streamlit app for TTF to EPDFont converter (Fixed Indexing Version)
"""

import streamlit as st
import freetype
import struct
import math
import os
import tempfile
from collections import namedtuple
from io import BytesIO

st.set_page_config(
    page_title="TTF to EPDFont 변환기",
    page_icon="⚡",
    layout="wide"
)

EPDFONT_MAGIC = 0x46445045  # "EPDF"
EPDFONT_VERSION = 1

# 글리프 속성 정의
GlyphProps = namedtuple("GlyphProps", ["width", "height", "advance_x", "left", "top", "data_length", "data_offset", "code_point"])

def norm_floor(val):
    return int(math.floor(val / (1 << 6)))

def norm_ceil(val):
    return int(math.ceil(val / (1 << 6)))

def load_glyph(font_stack, code_point):
    """폰트 스택에서 유효한 글리프를 로드합니다."""
    face_index = 0
    while face_index < len(font_stack):
        face = font_stack[face_index]
        glyph_index = face.get_char_index(code_point)
        if glyph_index > 0:
            face.load_glyph(glyph_index, freetype.FT_LOAD_RENDER)
            return face
        face_index += 1
    return None

def convert_ttf_to_epdfont(font_files, font_name, size, is_2bit=False, line_height=1.2, letter_spacing=0, width_scale=1.0, baseline_offset=0):
    """TTF를 .epdfont 바이너리 포맷으로 변환합니다."""

    font_stack = [freetype.Face(f) for f in font_files]

    for face in font_stack:
        face.set_pixel_sizes(0, size)

    # 기본 유니코드 구간 설정
    intervals = [
        (0x0000, 0x007F), (0x0080, 0x00FF), (0x0100, 0x017F), (0x0180, 0x024F),
        (0x0250, 0x02AF), (0x02B0, 0x02FF), (0x0300, 0x036F), (0x0370, 0x03FF),
        (0x0400, 0x04FF), (0x0500, 0x052F), (0x1100, 0x11FF), (0x3130, 0x318F),
        (0xA960, 0xA97F), (0xAC00, 0xD7AF), (0xD7B0, 0xD7FF), (0x3000, 0x303F),
        (0x3040, 0x309F), (0x30A0, 0x30FF), (0x3100, 0x312F), (0x31F0, 0x31FF),
        (0x3200, 0x32FF), (0x3300, 0x33FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
        (0xF900, 0xFAFF), (0xFF00, 0xFFEF), (0x2000, 0x206F), (0x2070, 0x209F),
        (0x20A0, 0x20CF), (0x20D0, 0x20FF), (0x2100, 0x214F), (0x2150, 0x218F),
        (0x2190, 0x21FF), (0x2200, 0x22FF), (0x2300, 0x23FF), (0x2400, 0x243F),
        (0x2440, 0x245F), (0x2460, 0x24FF), (0x2500, 0x257F), (0x2580, 0x259F),
        (0x25A0, 0x25FF), (0x2600, 0x26FF), (0x2700, 0x27BF), (0x27C0, 0x27EF),
        (0x27F0, 0x27FF), (0x2800, 0x28FF), (0x2900, 0x297F), (0x2980, 0x29FF),
        (0x2A00, 0x2AFF), (0x2B00, 0x2BFF), (0xFFF0, 0xFFFF), (0x1F300, 0x1F5FF),
        (0x1F600, 0x1F64F), (0x1F680, 0x1F6FF), (0x1F900, 0x1F9FF), (0x1FA00, 0x1FA6F),
        (0x1FA70, 0x1FAFF), (0x20000, 0x2A6DF), (0x2A700, 0x2B73F), (0x2B740, 0x2B81F),
        (0x2B820, 0x2CEAF), (0x2CEB0, 0x2EBEF), (0x2F800, 0x2FA1F),
    ]

    # [중요] 유니코드 구간 검증 로직 - 폰트에 없는 글자를 제외하고 구간을 재구성합니다.
    validated_intervals = []
    status_text = st.empty()
    status_text.text("유니코드 구간 검증 중...")
    
    for i_start, i_end in sorted(intervals):
        start = i_start
        for code_point in range(i_start, i_end + 1):
            face = load_glyph(font_stack, code_point)
            if face is None:
                if start < code_point:
                    validated_intervals.append((start, code_point - 1))
                start = code_point + 1
        if start <= i_end:
            validated_intervals.append((start, i_end))

    # 글리프 생성
    all_glyphs = []
    total_size = 0
    total_chars = sum(i_end - i_start + 1 for i_start, i_end in validated_intervals)
    processed_chars = 0
    progress_bar = st.progress(0)

    for i_start, i_end in validated_intervals:
        for code_point in range(i_start, i_end + 1):
            face = load_glyph(font_stack, code_point)
            if face is None:
                continue

            bitmap = face.glyph.bitmap
            
            # 4-bit 중계 버퍼 생성
            pixels4g = []
            px = 0
            for i, v in enumerate(bitmap.buffer):
                x = i % bitmap.width if bitmap.width > 0 else 0
                if x % 2 == 0:
                    px = (v >> 4)
                else:
                    px = px | (v & 0xF0)
                    pixels4g.append(px)
                    px = 0
                if bitmap.width > 0 and x == bitmap.width - 1 and bitmap.width % 2 > 0:
                    pixels4g.append(px)
                    px = 0

            # 1-bit(BW) 또는 2-bit(Gray) 패킹 로직
            if is_2bit:
                pixels = []
                temp_px = 0
                pitch = (bitmap.width // 2) + (bitmap.width % 2)
                for y in range(bitmap.rows):
                    for x in range(bitmap.width):
                        temp_px <<= 2
                        if pitch > 0 and len(pixels4g) > 0:
                            idx = y * pitch + (x // 2)
                            bm = pixels4g[idx] if idx < len(pixels4g) else 0
                            val = (bm >> ((x % 2) * 4)) & 0xF
                            if val >= 12: temp_px += 3
                            elif val >= 8: temp_px += 2
                            elif val >= 4: temp_px += 1
                        if (y * bitmap.width + x) % 4 == 3:
                            pixels.append(temp_px)
                            temp_px = 0
                if (bitmap.width * bitmap.rows) % 4 != 0:
                    temp_px <<= (4 - (bitmap.width * bitmap.rows) % 4) * 2
                    pixels.append(temp_px)
            else:
                pixels = []
                temp_px = 0
                pitch = (bitmap.width // 2) + (bitmap.width % 2)
                for y in range(bitmap.rows):
                    for x in range(bitmap.width):
                        temp_px <<= 1
                        if pitch > 0 and len(pixels4g) > 0:
                            idx = y * pitch + (x // 2)
                            bm = pixels4g[idx] if idx < len(pixels4g) else 0
                            temp_px += 1 if ((x & 1) == 0 and bm & 0x0E > 0) or ((x & 1) == 1 and bm & 0xE0 > 0) else 0
                        if (y * bitmap.width + x) % 8 == 7:
                            pixels.append(temp_px)
                            temp_px = 0
                if (bitmap.width * bitmap.rows) % 8 != 0:
                    temp_px <<= (8 - (bitmap.width * bitmap.rows) % 8)
                    pixels.append(temp_px)

            packed = bytes(pixels)
            orig_adv_x = norm_floor(face.glyph.advance.x)
            
            glyph = GlyphProps(
                width=bitmap.width,
                height=bitmap.rows,
                advance_x=int(orig_adv_x * width_scale) + letter_spacing,
                left=face.glyph.bitmap_left,
                top=face.glyph.bitmap_top + baseline_offset,
                data_length=len(packed),
                data_offset=total_size,
                code_point=code_point,
            )
            total_size += len(packed)
            all_glyphs.append((glyph, packed))
            
            processed_chars += 1
            if processed_chars % 100 == 0:
                progress_bar.progress(processed_chars / total_chars)
                status_text.text(f"변환 중... {processed_chars}/{total_chars} 글자")

    progress_bar.progress(1.0)
    status_text.text(f"✅ 변환 완료! {len(all_glyphs)}개 글리프 생성됨")

    # 폰트 메트릭 정보 가져오기
    face = load_glyph(font_stack, ord('|')) or font_stack[0]
    advance_y = int(norm_ceil(face.size.height) * line_height)
    ascender = norm_ceil(face.size.ascender)
    descender = norm_floor(face.size.descender)

    output = BytesIO()
    write_epdfont(output, validated_intervals, all_glyphs, advance_y, ascender, descender, is_2bit)
    output.seek(0)

    return output, {
        'glyphs': len(all_glyphs),
        'intervals': len(validated_intervals),
        'advance_y': advance_y,
        'ascender': ascender,
        'descender': descender,
        'file_size': len(output.getvalue())
    }

def write_epdfont(output, intervals, all_glyphs, advance_y, ascender, descender, is_2bit):
    """바이너리 헤더와 데이터를 구조에 맞게 기록합니다."""
    header_size = 32
    intervals_size = len(intervals) * 12
    glyphs_size = len(all_glyphs) * 16

    intervals_offset = header_size
    glyphs_offset = intervals_offset + intervals_size
    bitmap_offset = glyphs_offset + glyphs_size

    # 헤더 작성 (32바이트)
    header = struct.pack(
        '<IHBBBBBB5I',
        EPDFONT_MAGIC, EPDFONT_VERSION, 1 if is_2bit else 0, 0,
        advance_y & 0xFF, ascender & 0xFF, descender & 0xFF, 0,
        len(intervals), len(all_glyphs),
        intervals_offset, glyphs_offset, bitmap_offset,
    )
    output.write(header)

    # 유니코드 구간 정보 작성 - 글리프 인덱스(offset)를 정확히 계산합니다.
    current_glyph_idx = 0
    for i_start, i_end in intervals:
        output.write(struct.pack('<3I', i_start, i_end, current_glyph_idx))
        current_glyph_idx += (i_end - i_start + 1)

    # 글리프 메타데이터 작성
    for glyph, _ in all_glyphs:
        output.write(struct.pack(
            '<4B2h2I',
            glyph.width, glyph.height, glyph.advance_x, 0,
            glyph.left, glyph.top, glyph.data_length, glyph.data_offset,
        ))

    # 비트맵 데이터 작성
    for _, packed in all_glyphs:
        output.write(packed)

# --- Streamlit UI 구성 ---
st.title("⚡ TTF to EPDFont 변환기")
uploaded_file = st.file_uploader("폰트 파일 업로드 (TTF/OTF)", type=['ttf', 'otf'])

if uploaded_file is not None:
    col1, col2 = st.columns(2)
    with col1:
        font_name = st.text_input("폰트 이름", value="font")
        font_size = st.number_input("폰트 크기 (픽셀)", min_value=8, max_value=128, value=28)
        is_2bit = st.checkbox("2비트 그레이스케일", value=False)
    with col2:
        line_height = st.number_input("줄 높이 배율", value=1.2, step=0.1)
        letter_spacing = st.number_input("자간 (픽셀)", value=0)
        width_scale = st.number_input("장평 (비율)", value=1.0, step=0.1)
        baseline_offset = st.number_input("베이스라인 오프셋", value=0)
    
    if st.button("🚀 변환 시작", type="primary", use_container_width=True):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        try:
            output_buffer, stats = convert_ttf_to_epdfont(
                [tmp_path], font_name, font_size, is_2bit, 
                line_height, letter_spacing, width_scale, baseline_offset
            )
            st.success("✅ 변환이 완료되었습니다!")
            st.download_button(
                label="⬇️ 폰트 다운로드",
                data=output_buffer.getvalue(),
                file_name=f"{font_name}_{font_size}.epdfont",
                mime="application/octet-stream",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)