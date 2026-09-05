#!/usr/bin/env python3
"""Build the deterministic synthetic clean_env_v1 environment."""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
ENV_ROOT = CLEAN_ROOT / "environment"
MANIFEST_ROOT = CLEAN_ROOT / "manifests"
SEED = 2026
GENERATOR_VERSION = "clean_env_generator_v1"

DEPARTMENTS = (
    ("CNTT", "Công nghệ thông tin"),
    ("KINHTE", "Kinh tế"),
    ("NGONNGU", "Ngôn ngữ"),
    ("DIENTU", "Điện tử"),
    ("XAYDUNG", "Xây dựng"),
    ("LUAT", "Luật"),
    ("YDUOC", "Y dược"),
    ("MOITRUONG", "Môi trường"),
    ("DULICH", "Du lịch"),
    ("MYTHUAT", "Mỹ thuật"),
)


def _doc(
    number: int,
    domain: str,
    title: str,
    content: str,
    facts: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, Any]]:
    doc_id = f"CDOC_{number:03d}"
    return (
        {"doc_id": doc_id, "title": title, "content": content},
        {
            "source_type": "document",
            "source_id": doc_id,
            "domain": domain,
            "title": title,
            "facts": facts,
        },
    )


def build_documents() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    records: list[tuple[str, str, str, list[tuple[str, str, Any, str]]]] = [
        (
            "course_registration",
            "Kế hoạch đăng ký học phần kỳ 1 năm 2026",
            (
                "Cổng đăng ký mở ngày 2026-08-15, đóng ngày 2026-08-22. "
                "Sinh viên được đăng ký tối đa 24 tín chỉ."
            ),
            [
                ("open", "date", "2026-08-15", "date_equal"),
                ("close", "date", "2026-08-22", "date_equal"),
                ("max_credits", "number", 24, "numeric_equal"),
            ],
        ),
        (
            "course_registration",
            "Thông báo đăng ký học phần kỳ 2 năm 2026",
            "Đợt đăng ký bắt đầu 2026-12-05 và kết thúc 2026-12-12; giới hạn là 22 tín chỉ.",
            [
                ("open", "date", "2026-12-05", "date_equal"),
                ("close", "date", "2026-12-12", "date_equal"),
                ("max_credits", "number", 22, "numeric_equal"),
            ],
        ),
        (
            "course_registration",
            "Hướng dẫn học kỳ hè 2026",
            "Sinh viên đăng ký học kỳ hè từ 2026-05-20 đến 2026-05-27, không quá 12 tín chỉ.",
            [
                ("open", "date", "2026-05-20", "date_equal"),
                ("close", "date", "2026-05-27", "date_equal"),
                ("max_credits", "number", 12, "numeric_equal"),
            ],
        ),
        (
            "course_registration",
            "Quy trình điều chỉnh môn học 2026",
            (
                "Thời hạn thêm hoặc rút học phần là 2026-09-05. "
                "Mỗi yêu cầu được xử lý trong 3 ngày làm việc."
            ),
            [
                ("adjust_deadline", "date", "2026-09-05", "date_equal"),
                ("processing_days", "number", 3, "numeric_equal"),
            ],
        ),
        (
            "course_registration",
            "Đăng ký học cải thiện",
            "Điểm tối thiểu để đăng ký học cải thiện là 5.0 và hồ sơ nộp trước 2026-09-12.",
            [
                ("minimum_grade", "number", 5.0, "numeric_equal"),
                ("deadline", "date", "2026-09-12", "date_equal"),
            ],
        ),
        (
            "academic_calendar",
            "Lịch thi học kỳ 1 năm 2026",
            "Kỳ thi bắt đầu 2026-12-10 và kết thúc 2026-12-20. Sinh viên có mặt sớm 20 phút.",
            [
                ("exam_start", "date", "2026-12-10", "date_equal"),
                ("exam_end", "date", "2026-12-20", "date_equal"),
                ("arrival_minutes", "number", 20, "numeric_equal"),
            ],
        ),
        (
            "academic_calendar",
            "Lịch nghỉ Tết Dương lịch 2027",
            "Toàn trường nghỉ từ 2027-01-01 đến hết 2027-01-03.",
            [
                ("holiday_start", "date", "2027-01-01", "date_equal"),
                ("holiday_end", "date", "2027-01-03", "date_equal"),
            ],
        ),
        (
            "academic_calendar",
            "Tuần sinh hoạt công dân 2026",
            "Chương trình diễn ra ngày 2026-08-08 tại hội trường H1, bắt đầu lúc 08:00.",
            [
                ("event_date", "date", "2026-08-08", "date_equal"),
                ("location", "string", "H1", "case_insensitive"),
            ],
        ),
        (
            "academic_calendar",
            "Lịch bảo vệ đồ án đợt tháng 6",
            "Sinh viên bảo vệ đồ án từ 2027-06-12 đến 2027-06-16 tại khu D.",
            [
                ("defense_start", "date", "2027-06-12", "date_equal"),
                ("defense_end", "date", "2027-06-16", "date_equal"),
                ("location", "string", "khu D", "substring_normalized"),
            ],
        ),
        (
            "academic_calendar",
            "Mốc khóa sổ điểm năm học 2026–2027",
            "Giảng viên hoàn tất nhập điểm trước 17:00 ngày 2027-01-15.",
            [("grade_deadline", "date", "2027-01-15", "date_equal")],
        ),
        (
            "tuition",
            "Biểu phí chương trình chuẩn 2026",
            "Học phí là 820000 đồng mỗi tín chỉ. Hạn thanh toán kỳ 1 là 2026-09-10.",
            [
                ("fee_per_credit", "money", 820000, "numeric_equal"),
                ("payment_deadline", "date", "2026-09-10", "date_equal"),
            ],
        ),
        (
            "tuition",
            "Biểu phí chương trình chất lượng cao 2026",
            "Mức thu là 1450000 đồng mỗi tín chỉ; hạn kỳ 1 là 2026-09-12.",
            [
                ("fee_per_credit", "money", 1450000, "numeric_equal"),
                ("payment_deadline", "date", "2026-09-12", "date_equal"),
            ],
        ),
        (
            "tuition",
            "Chính sách miễn giảm học phí",
            "Sinh viên thuộc diện A được giảm 70 phần trăm; diện B được giảm 50 phần trăm.",
            [
                ("discount_a", "number", 70, "numeric_equal"),
                ("discount_b", "number", 50, "numeric_equal"),
            ],
        ),
        (
            "tuition",
            "Quy định hoàn học phí",
            (
                "Yêu cầu hoàn học phí nộp trong 14 ngày kể từ ngày rút học phần; "
                "thời gian xử lý là 10 ngày làm việc."
            ),
            [
                ("request_window_days", "number", 14, "numeric_equal"),
                ("processing_days", "number", 10, "numeric_equal"),
            ],
        ),
        (
            "tuition",
            "Phí dịch vụ học vụ 2026",
            "Cấp bảng điểm bản giấy có phí 30000 đồng; xác nhận sinh viên có phí 20000 đồng.",
            [
                ("transcript_fee", "money", 30000, "numeric_equal"),
                ("confirmation_fee", "money", 20000, "numeric_equal"),
            ],
        ),
        (
            "scholarships",
            "Học bổng khuyến khích học tập",
            "Điểm trung bình tối thiểu là 8.0, điểm rèn luyện tối thiểu 80; hạn hồ sơ 2026-09-30.",
            [
                ("minimum_gpa", "number", 8.0, "numeric_equal"),
                ("minimum_conduct", "number", 80, "numeric_equal"),
                ("deadline", "date", "2026-09-30", "date_equal"),
            ],
        ),
        (
            "scholarships",
            "Học bổng tài năng công nghệ",
            (
                "Ứng viên cần GPA từ 8.5 và nộp hồ sơ trước 2026-10-05. "
                "Giá trị học bổng là 15000000 đồng."
            ),
            [
                ("minimum_gpa", "number", 8.5, "numeric_equal"),
                ("deadline", "date", "2026-10-05", "date_equal"),
                ("amount", "money", 15000000, "numeric_equal"),
            ],
        ),
        (
            "scholarships",
            "Quỹ hỗ trợ sinh viên vượt khó",
            "Mức hỗ trợ một lần là 5000000 đồng. Hồ sơ tiếp nhận đến 2026-10-12.",
            [
                ("amount", "money", 5000000, "numeric_equal"),
                ("deadline", "date", "2026-10-12", "date_equal"),
            ],
        ),
        (
            "scholarships",
            "Học bổng trao đổi Đông Nam Á",
            "Yêu cầu ngoại ngữ bậc 4 và tối thiểu 60 tín chỉ tích lũy; hạn đăng ký 2026-11-01.",
            [
                ("language_level", "number", 4, "numeric_equal"),
                ("minimum_credits", "number", 60, "numeric_equal"),
                ("deadline", "date", "2026-11-01", "date_equal"),
            ],
        ),
        (
            "scholarships",
            "Học bổng nghiên cứu sinh viên",
            "Mỗi nhóm được hỗ trợ tối đa 12000000 đồng và phải nộp đề cương trước 2026-10-20.",
            [
                ("maximum_amount", "money", 12000000, "numeric_equal"),
                ("deadline", "date", "2026-10-20", "date_equal"),
            ],
        ),
        (
            "graduation",
            "Chuẩn tốt nghiệp chương trình CNTT",
            "Sinh viên CNTT cần 130 tín chỉ và ngoại ngữ bậc 3 để xét tốt nghiệp.",
            [
                ("required_credits", "number", 130, "numeric_equal"),
                ("language_level", "number", 3, "numeric_equal"),
            ],
        ),
        (
            "graduation",
            "Chuẩn tốt nghiệp chương trình Kinh tế",
            "Chương trình Kinh tế yêu cầu 125 tín chỉ và chứng chỉ tin học cơ bản.",
            [
                ("required_credits", "number", 125, "numeric_equal"),
                ("it_certificate", "boolean", True, "boolean_equal"),
            ],
        ),
        (
            "graduation",
            "Thủ tục xét tốt nghiệp tháng 6 năm 2027",
            "Hồ sơ nộp trước 2027-05-15; kết quả dự kiến công bố 2027-06-25.",
            [
                ("deadline", "date", "2027-05-15", "date_equal"),
                ("result_date", "date", "2027-06-25", "date_equal"),
            ],
        ),
        (
            "graduation",
            "Quy định đồ án tốt nghiệp",
            "Đồ án tốt nghiệp có giá trị 10 tín chỉ và thời lượng thực hiện 16 tuần.",
            [
                ("project_credits", "number", 10, "numeric_equal"),
                ("duration_weeks", "number", 16, "numeric_equal"),
            ],
        ),
        (
            "graduation",
            "Cấp bằng và bảng điểm",
            "Bằng được phát sau quyết định công nhận 30 ngày; bảng điểm điện tử được cấp miễn phí.",
            [
                ("degree_days", "number", 30, "numeric_equal"),
                ("digital_transcript_free", "boolean", True, "boolean_equal"),
            ],
        ),
        (
            "student_services",
            "Thủ tục cấp lại thẻ sinh viên",
            "Lệ phí cấp lại thẻ là 60000 đồng; thời gian trả thẻ là 5 ngày làm việc.",
            [
                ("replacement_fee", "money", 60000, "numeric_equal"),
                ("processing_days", "number", 5, "numeric_equal"),
            ],
        ),
        (
            "student_services",
            "Quy trình xác nhận sinh viên",
            "Xác nhận điện tử được xử lý trong 2 ngày làm việc và có hiệu lực 90 ngày.",
            [
                ("processing_days", "number", 2, "numeric_equal"),
                ("valid_days", "number", 90, "numeric_equal"),
            ],
        ),
        (
            "student_services",
            "Dịch vụ tư vấn tâm lý",
            "Phòng tư vấn mở từ 08:30 đến 16:30 thứ Hai đến thứ Sáu tại phòng S105.",
            [
                ("close_time", "string", "16:30", "exact_normalized"),
                ("room", "string", "S105", "case_insensitive"),
            ],
        ),
        (
            "student_services",
            "Hỗ trợ sinh viên khuyết tật",
            "Yêu cầu hỗ trợ học tập cần gửi trước buổi học 3 ngày qua Phòng Công tác sinh viên.",
            [
                ("notice_days", "number", 3, "numeric_equal"),
                ("office", "string", "Phòng Công tác sinh viên", "substring_normalized"),
            ],
        ),
        (
            "student_services",
            "Quy trình phản ánh học vụ",
            "Phản ánh có mã theo dõi và được phản hồi trong 7 ngày làm việc.",
            [("response_days", "number", 7, "numeric_equal")],
        ),
        (
            "facilities",
            "Giờ hoạt động thư viện trung tâm",
            "Thư viện mở 07:00–21:00 từ thứ Hai đến thứ Bảy; Chủ nhật đóng cửa.",
            [
                ("close_time", "string", "21:00", "exact_normalized"),
                ("sunday_open", "boolean", False, "boolean_equal"),
            ],
        ),
        (
            "facilities",
            "Quy định phòng học tự quản",
            "Phòng tự học F201 có 80 chỗ và mở đến 22:00 mỗi ngày.",
            [
                ("capacity", "number", 80, "numeric_equal"),
                ("close_time", "string", "22:00", "exact_normalized"),
            ],
        ),
        (
            "facilities",
            "Hướng dẫn đặt phòng họp",
            "Đơn vị gửi yêu cầu trước 2 ngày; mỗi lượt đặt tối đa 3 giờ.",
            [
                ("notice_days", "number", 2, "numeric_equal"),
                ("maximum_hours", "number", 3, "numeric_equal"),
            ],
        ),
        (
            "facilities",
            "Bản đồ khu thí nghiệm",
            "Phòng Lab AI là D402, Lab Mạng là D305 và Lab Điện tử là E210.",
            [
                ("ai_lab", "string", "D402", "case_insensitive"),
                ("network_lab", "string", "D305", "case_insensitive"),
            ],
        ),
        (
            "facilities",
            "Quy định mượn thiết bị",
            "Laptop được mượn tối đa 4 giờ; tiền đặt cọc giả lập là 500000 đồng.",
            [
                ("maximum_hours", "number", 4, "numeric_equal"),
                ("deposit", "money", 500000, "numeric_equal"),
            ],
        ),
        (
            "administration",
            "Danh bạ Phòng Đào tạo",
            "Phòng Đào tạo ở A102, email daotao@university.example và máy lẻ 110.",
            [
                ("room", "string", "A102", "case_insensitive"),
                ("extension", "number", 110, "numeric_equal"),
            ],
        ),
        (
            "administration",
            "Danh bạ Phòng Công tác sinh viên",
            "Đơn vị ở B105, email ctsv@university.example và máy lẻ 120.",
            [
                ("room", "string", "B105", "case_insensitive"),
                ("extension", "number", 120, "numeric_equal"),
            ],
        ),
        (
            "administration",
            "Danh bạ Phòng Tài chính",
            "Phòng Tài chính ở A205, email taichinh@university.example và máy lẻ 130.",
            [
                ("room", "string", "A205", "case_insensitive"),
                ("extension", "number", 130, "numeric_equal"),
            ],
        ),
        (
            "administration",
            "Giờ tiếp sinh viên của khoa",
            "Văn phòng khoa tiếp sinh viên 09:00–11:00 thứ Ba và thứ Năm.",
            [
                ("start_time", "string", "09:00", "exact_normalized"),
                ("end_time", "string", "11:00", "exact_normalized"),
            ],
        ),
        (
            "administration",
            "Quy trình tiếp nhận hồ sơ một cửa",
            "Bộ phận một cửa cấp biên nhận ngay và xử lý hồ sơ thường trong 4 ngày làm việc.",
            [("processing_days", "number", 4, "numeric_equal")],
        ),
        (
            "dormitory",
            "Đăng ký ký túc xá năm học 2026–2027",
            "Cổng đăng ký mở 2026-07-20, đóng 2026-07-31; kết quả công bố 2026-08-05.",
            [
                ("open", "date", "2026-07-20", "date_equal"),
                ("close", "date", "2026-07-31", "date_equal"),
                ("result_date", "date", "2026-08-05", "date_equal"),
            ],
        ),
        (
            "dormitory",
            "Biểu phí ký túc xá khu A",
            "Phòng bốn người có phí 750000 đồng mỗi tháng; tiền cọc là 1000000 đồng.",
            [
                ("monthly_fee", "money", 750000, "numeric_equal"),
                ("deposit", "money", 1000000, "numeric_equal"),
            ],
        ),
        (
            "dormitory",
            "Nội quy giờ ra vào ký túc xá",
            "Cổng ký túc xá đóng lúc 23:00 và mở lại lúc 05:30.",
            [
                ("close_time", "string", "23:00", "exact_normalized"),
                ("open_time", "string", "05:30", "exact_normalized"),
            ],
        ),
        (
            "dormitory",
            "Dịch vụ giặt sấy ký túc xá",
            "Một lượt giặt có giá 20000 đồng, một lượt sấy có giá 15000 đồng.",
            [
                ("wash_fee", "money", 20000, "numeric_equal"),
                ("dry_fee", "money", 15000, "numeric_equal"),
            ],
        ),
        (
            "dormitory",
            "Quy trình báo hỏng phòng ở",
            "Sự cố điện nước khẩn cấp được phản hồi trong 2 giờ; sự cố thường trong 24 giờ.",
            [
                ("urgent_hours", "number", 2, "numeric_equal"),
                ("normal_hours", "number", 24, "numeric_equal"),
            ],
        ),
        (
            "activities",
            "Ngày hội câu lạc bộ 2026",
            "Ngày hội diễn ra 2026-09-05 tại sân trung tâm, có 35 câu lạc bộ tham gia.",
            [
                ("event_date", "date", "2026-09-05", "date_equal"),
                ("club_count", "number", 35, "numeric_equal"),
            ],
        ),
        (
            "activities",
            "Chương trình hiến máu mùa thu",
            "Chương trình tổ chức 2026-09-18 tại hội trường H2, chỉ tiêu 300 người.",
            [
                ("event_date", "date", "2026-09-18", "date_equal"),
                ("target_people", "number", 300, "numeric_equal"),
            ],
        ),
        (
            "activities",
            "Cuộc thi ý tưởng đổi mới sáng tạo",
            "Hạn nộp ý tưởng là 2026-10-25; giải nhất trị giá 20000000 đồng.",
            [
                ("deadline", "date", "2026-10-25", "date_equal"),
                ("first_prize", "money", 20000000, "numeric_equal"),
            ],
        ),
        (
            "activities",
            "Giải chạy sinh viên 2026",
            "Cự ly phong trào là 5 km; đăng ký trước 2026-11-10.",
            [
                ("distance_km", "number", 5, "numeric_equal"),
                ("deadline", "date", "2026-11-10", "date_equal"),
            ],
        ),
        (
            "activities",
            "Quy định hỗ trợ sự kiện sinh viên",
            "Mỗi sự kiện được hỗ trợ tối đa 8000000 đồng và hồ sơ nộp trước 15 ngày.",
            [
                ("maximum_amount", "money", 8000000, "numeric_equal"),
                ("notice_days", "number", 15, "numeric_equal"),
            ],
        ),
    ]
    documents: list[dict[str, str]] = []
    catalog: list[dict[str, Any]] = []
    for number, (domain, title, content, raw_facts) in enumerate(records, 1):
        facts = [
            {"fact_id": fact_id, "type": fact_type, "value": value, "comparator": comparator}
            for fact_id, fact_type, value, comparator in raw_facts
        ]
        document, entry = _doc(number, domain, title, content, facts)
        documents.append(document)
        catalog.append(entry)
    return documents, catalog


def build_pages() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    topics = [
        (
            "transport",
            "Xe buýt đến cơ sở A",
            "Các tuyến 08, 18 và 50 dừng gần cổng A.",
            "routes",
            "set",
            ["08", "18", "50"],
            "set_equal",
        ),
        (
            "transport",
            "Lịch xe nội bộ cơ sở B",
            "Xe rời cơ sở B lúc 07:15, 12:15 và 17:15.",
            "times",
            "set",
            ["07:15", "12:15", "17:15"],
            "set_equal",
        ),
        (
            "facilities",
            "Tình trạng phòng tự học",
            "Phòng F201 còn 42 chỗ trống lúc 14:00.",
            "available_seats",
            "number",
            42,
            "numeric_equal",
        ),
        (
            "facilities",
            "Lịch bảo trì cổng học vụ",
            "Cổng học vụ bảo trì từ 22:00 ngày 2026-08-12 đến 01:00 ngày 2026-08-13.",
            "maintenance_date",
            "date",
            "2026-08-12",
            "date_equal",
        ),
        (
            "student_services",
            "Kênh hỗ trợ kỹ thuật",
            "Kênh chat hỗ trợ hoạt động đến 18:00 các ngày làm việc.",
            "close_time",
            "string",
            "18:00",
            "exact_normalized",
        ),
        (
            "student_services",
            "Lịch tư vấn tuyển dụng",
            "Phiên tư vấn diễn ra ngày 2026-09-22 tại phòng C301.",
            "event_date",
            "date",
            "2026-09-22",
            "date_equal",
        ),
        (
            "activities",
            "Thông báo hội sách",
            "Hội sách mở ngày 2026-10-02 tại sân thư viện.",
            "event_date",
            "date",
            "2026-10-02",
            "date_equal",
        ),
        (
            "activities",
            "Đăng ký câu lạc bộ nhiếp ảnh",
            "Câu lạc bộ nhận đăng ký đến 2026-09-25.",
            "deadline",
            "date",
            "2026-09-25",
            "date_equal",
        ),
        (
            "dormitory",
            "Xe đưa đón ký túc xá",
            "Chuyến cuối từ trường về ký túc xá rời lúc 21:30.",
            "last_departure",
            "string",
            "21:30",
            "exact_normalized",
        ),
        (
            "dormitory",
            "Thực đơn căn tin khu ở",
            "Suất ăn tiêu chuẩn có giá 32000 đồng.",
            "meal_price",
            "money",
            32000,
            "numeric_equal",
        ),
        (
            "academic_calendar",
            "Lịch nghỉ Quốc khánh 2026",
            "Trường nghỉ từ 2026-09-02 đến hết 2026-09-03.",
            "holiday_end",
            "date",
            "2026-09-03",
            "date_equal",
        ),
        (
            "academic_calendar",
            "Lịch nghỉ Tết Nguyên đán 2027",
            "Sinh viên nghỉ từ 2027-02-05 đến 2027-02-14.",
            "holiday_start",
            "date",
            "2027-02-05",
            "date_equal",
        ),
        (
            "tuition",
            "Hướng dẫn thanh toán trực tuyến",
            "Giao dịch được đối soát trong tối đa 2 ngày làm việc.",
            "processing_days",
            "number",
            2,
            "numeric_equal",
        ),
        (
            "tuition",
            "Lịch hỗ trợ học phí",
            "Quầy hỗ trợ học phí đóng lúc 16:00 thứ Sáu.",
            "close_time",
            "string",
            "16:00",
            "exact_normalized",
        ),
        (
            "scholarships",
            "Hội thảo viết hồ sơ học bổng",
            "Hội thảo bắt đầu 09:00 ngày 2026-09-15.",
            "event_date",
            "date",
            "2026-09-15",
            "date_equal",
        ),
        (
            "scholarships",
            "Kết quả học bổng cộng đồng",
            "Có 28 sinh viên nhận học bổng cộng đồng đợt 1.",
            "recipient_count",
            "number",
            28,
            "numeric_equal",
        ),
        (
            "graduation",
            "Lịch chụp ảnh tốt nghiệp",
            "Buổi chụp ảnh tập thể diễn ra ngày 2027-05-20.",
            "event_date",
            "date",
            "2027-05-20",
            "date_equal",
        ),
        (
            "graduation",
            "Hướng dẫn nhận lễ phục",
            "Sinh viên nhận lễ phục tại D101 trước lễ 2 ngày.",
            "room",
            "string",
            "D101",
            "case_insensitive",
        ),
        (
            "course_registration",
            "Trạng thái cổng đăng ký",
            "Cổng đăng ký dự kiến mở lại lúc 06:00 ngày 2026-08-13.",
            "reopen_time",
            "string",
            "06:00",
            "exact_normalized",
        ),
        (
            "course_registration",
            "Hỗ trợ đăng ký môn",
            "Hotline giả lập hỗ trợ đến 19:00 trong tuần đăng ký.",
            "close_time",
            "string",
            "19:00",
            "exact_normalized",
        ),
        (
            "administration",
            "Lịch làm việc bộ phận một cửa",
            "Bộ phận một cửa nghỉ trưa từ 12:00 đến 13:30.",
            "reopen_time",
            "string",
            "13:30",
            "exact_normalized",
        ),
        (
            "administration",
            "Thông báo chuyển phòng Tài chính",
            "Phòng Tài chính tạm làm việc tại A207 từ 2026-09-01.",
            "room",
            "string",
            "A207",
            "case_insensitive",
        ),
        (
            "facilities",
            "Chỉ số sử dụng thư viện",
            "Tháng 8 có 12500 lượt vào thư viện.",
            "visitor_count",
            "number",
            12500,
            "numeric_equal",
        ),
        (
            "activities",
            "Lịch chiếu phim sinh viên",
            "Phim bắt đầu lúc 18:30 ngày 2026-10-08 tại H3.",
            "start_time",
            "string",
            "18:30",
            "exact_normalized",
        ),
        (
            "transport",
            "Bãi gửi xe cơ sở A",
            "Bãi xe đóng lúc 22:30; phí lượt xe máy là 5000 đồng.",
            "parking_fee",
            "money",
            5000,
            "numeric_equal",
        ),
    ]
    pages: list[dict[str, str]] = []
    catalog: list[dict[str, Any]] = []
    for number, (domain, title, content, fact_id, fact_type, value, comparator) in enumerate(
        topics, 1
    ):
        page_id = f"CPAGE_{number:03d}"
        pages.append(
            {
                "page_id": page_id,
                "title": title,
                "content": content,
                "source_url": f"https://synthetic-university.invalid/page/{number:03d}",
            }
        )
        catalog.append(
            {
                "source_type": "cached_page",
                "source_id": page_id,
                "domain": domain,
                "title": title,
                "facts": [
                    {
                        "fact_id": fact_id,
                        "type": fact_type,
                        "value": value,
                        "comparator": comparator,
                    }
                ],
            }
        )
    return pages, catalog


def build_database_seed() -> dict[str, list[list[Any]]]:
    rng = random.Random(SEED)  # noqa: S311 - deterministic synthetic fixture generation
    course_prefixes = ("CS", "BA", "EN", "EE", "CE", "LAW", "MED", "ENV", "TR", "ART")
    courses: list[list[Any]] = []
    for department_index, (department_id, _) in enumerate(DEPARTMENTS):
        prefix = course_prefixes[department_index]
        for level in range(1, 7):
            code = f"{prefix}{level}0{department_index + 1}"
            courses.append([code, f"Học phần giả lập {code}", 2 + (level % 3), department_id])

    rooms = [
        [
            f"ROOM_{index:03d}",
            f"{chr(65 + (index % 6))}{100 + index}",
            30 + (index % 6) * 10,
            f"Cơ sở {(index % 3) + 1}",
        ]
        for index in range(1, 31)
    ]
    sections: list[list[Any]] = []
    for index, course in enumerate(courses, 1):
        room = rooms[(index * 3) % len(rooms)]
        term = "2026-1" if index % 2 else "2026-2"
        sections.append([f"SEC_{index:03d}", course[0], term, room[0], 25 + index % 36])
        if index <= 20:
            sections.append(
                [
                    f"SEC_{index + 60:03d}",
                    course[0],
                    "2027-1",
                    rooms[index % 30][0],
                    30 + index % 31,
                ]
            )

    students = []
    for index in range(1, 101):
        department_id = DEPARTMENTS[(index - 1) % len(DEPARTMENTS)][0]
        program = "standard" if index % 3 else "high_quality"
        students.append(
            [
                f"SV2026{index:04d}",
                f"Sinh viên Giả lập {index:03d}",
                department_id,
                program,
                round(6.0 + rng.randint(0, 30) / 10, 1),
            ]
        )

    registrations = []
    for index in range(1, 201):
        student = students[(index * 7) % len(students)][0]
        section = sections[(index * 11) % len(sections)][0]
        status = "registered" if index % 5 else "waitlist"
        registrations.append([f"REG_{index:04d}", student, section, status])

    scholarships = []
    scholarship_types = ("encouragement", "talent", "community", "research")
    for index in range(1, 41):
        scholarships.append(
            [
                f"SCH_{index:03d}",
                students[(index * 2) % 100][0],
                scholarship_types[index % 4],
                3000000 + (index % 5) * 1000000,
                "2026-1",
            ]
        )

    staff = []
    for index in range(1, 41):
        department_id = DEPARTMENTS[(index - 1) % 10][0]
        staff.append(
            [
                f"STAFF_{index:03d}",
                f"Cán bộ Giả lập {index:03d}",
                department_id,
                f"staff{index:03d}@university.example",
                200 + index,
            ]
        )

    return {
        "departments": [[department_id, name] for department_id, name in DEPARTMENTS],
        "courses": courses,
        "rooms": rooms,
        "course_sections": sections,
        "students": students,
        "registrations": registrations,
        "scholarships": scholarships,
        "staff_directory": staff,
    }


SCHEMA = (
    "CREATE TABLE departments (department_id TEXT PRIMARY KEY, department_name TEXT)",
    (
        "CREATE TABLE courses (course_code TEXT PRIMARY KEY, course_name TEXT, "
        "credits INTEGER, department_id TEXT)"
    ),
    (
        "CREATE TABLE rooms (room_id TEXT PRIMARY KEY, room_code TEXT, "
        "capacity INTEGER, campus TEXT)"
    ),
    (
        "CREATE TABLE course_sections (section_id TEXT PRIMARY KEY, course_code TEXT, "
        "term TEXT, room_id TEXT, capacity INTEGER)"
    ),
    (
        "CREATE TABLE students (student_id TEXT PRIMARY KEY, student_name TEXT, "
        "department_id TEXT, program TEXT, gpa REAL)"
    ),
    (
        "CREATE TABLE registrations (registration_id TEXT PRIMARY KEY, student_id TEXT, "
        "section_id TEXT, status TEXT)"
    ),
    (
        "CREATE TABLE scholarships (scholarship_id TEXT PRIMARY KEY, student_id TEXT, "
        "scholarship_type TEXT, amount INTEGER, term TEXT)"
    ),
    (
        "CREATE TABLE staff_directory (staff_id TEXT PRIMARY KEY, staff_name TEXT, "
        "department_id TEXT, email TEXT, extension INTEGER)"
    ),
)

INSERTS = {
    "departments": "INSERT INTO departments VALUES (?, ?)",
    "courses": "INSERT INTO courses VALUES (?, ?, ?, ?)",
    "rooms": "INSERT INTO rooms VALUES (?, ?, ?, ?)",
    "course_sections": "INSERT INTO course_sections VALUES (?, ?, ?, ?, ?)",
    "students": "INSERT INTO students VALUES (?, ?, ?, ?, ?)",
    "registrations": "INSERT INTO registrations VALUES (?, ?, ?, ?)",
    "scholarships": "INSERT INTO scholarships VALUES (?, ?, ?, ?, ?)",
    "staff_directory": "INSERT INTO staff_directory VALUES (?, ?, ?, ?, ?)",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    from react_agent.validation.clean_integrity import assert_clean_version_writable

    assert_clean_version_writable(CLEAN_ROOT)
    documents, document_catalog = build_documents()
    pages, page_catalog = build_pages()
    seed = build_database_seed()
    document_dir = ENV_ROOT / "documents"
    page_dir = ENV_ROOT / "cached_pages"
    database_dir = ENV_ROOT / "database"
    for directory in (document_dir, page_dir, database_dir, MANIFEST_ROOT):
        directory.mkdir(parents=True, exist_ok=True)

    document_path = document_dir / "documents.json"
    page_path = page_dir / "pages.json"
    seed_path = database_dir / "seed.json"
    database_path = database_dir / "university.db"
    catalog_path = MANIFEST_ROOT / "source_catalog.json"
    document_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    page_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_path.write_text(
        json.dumps(document_catalog + page_catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    temporary_path = database_dir / ".university.tmp.db"
    temporary_path.unlink(missing_ok=True)
    with sqlite3.connect(temporary_path) as connection:
        for statement in SCHEMA:
            connection.execute(statement)
        for table, statement in INSERTS.items():
            connection.executemany(statement, seed[table])
        connection.commit()
    temporary_path.replace(database_path)

    manifest = {
        "environment_version": "clean_env_v1",
        "generator_version": GENERATOR_VERSION,
        "seed": SEED,
        "synthetic": True,
        "internet_required": False,
        "documents": len(documents),
        "cached_pages": len(pages),
        "database_tables": {table: len(seed[table]) for table in INSERTS},
        "files": {
            str(path.relative_to(CLEAN_ROOT)): sha256(path)
            for path in (document_path, page_path, seed_path, database_path, catalog_path)
        },
    }
    manifest_path = MANIFEST_ROOT / "environment_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Built clean_env_v1: {len(documents)} documents, {len(pages)} cached pages, "
        f"{len(INSERTS)} SQLite tables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
