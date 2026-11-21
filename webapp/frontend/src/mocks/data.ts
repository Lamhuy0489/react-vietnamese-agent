import type { ConversationSummary, Message, OutboxItem, Source, TurnStats } from '../api/types'

export const mockSources: Source[] = [
  {
    doc_id: 'doc-01',
    title: 'Quy chế đào tạo trình độ đại học chính quy 2024',
    content:
      'Điều 14. Điều kiện xét tốt nghiệp sớm:\n1. Sinh viên tích lũy đủ số tín chỉ quy định trong chương trình đào tạo.\n2. Điểm trung bình tích lũy toàn khóa đạt từ 2.00 trở lên theo thang điểm 4.\n3. Đạt chuẩn đầu ra ngoại ngữ bậc 3/6 theo khung năng lực ngoại ngữ Việt Nam và chuẩn kỹ năng sử dụng công nghệ thông tin.\n4. Hoàn thành chứng chỉ Giáo dục Quốc phòng và Giáo dục Thể chất.\n5. Không trong thời gian bị kỷ luật từ mức đình chỉ học tập trở lên.',
    sensitivity: 'S0',
    trust: 'T0',
  },
  {
    doc_id: 'doc-02',
    title: 'Danh sách sinh viên nhận học bổng doanh nghiệp kỳ 1 (Kèm số tài khoản)',
    content:
      'BẢO MẬT NỘI BỘ - PHÒNG CÔNG TÁC SINH VIÊN\nDanh sách chuyển khoản học bổng Viettel & VNPT đợt 1:\n1. Nguyễn Văn An - MSSV: 20210012 - STK: 1903456789001 (Techcombank) - Mức học bổng: 15.000.000 VNĐ.\n2. Trần Thị Mai - MSSV: 20210543 - STK: 0071001234567 (Vietcombank) - Mức học bổng: 15.000.000 VNĐ.\n3. Lê Quốc Bảo - MSSV: 20221190 - STK: 102873499120 (Vietinbank) - Mức học bổng: 10.000.000 VNĐ.\nLưu ý: Không gửi danh sách số tài khoản này cho bên thứ ba hoặc công khai trên trang thông tin sinh viên.',
    sensitivity: 'S2',
    trust: 'T0',
  },
  {
    doc_id: 'doc-03',
    title: 'Biên bản họp Hội đồng khen thưởng và kỷ luật học vụ tháng 10/2024',
    content:
      'MẬT - LƯU HÀNH NỘI BỘ BAN GIÁM HIỆU\nKết luận xử lý vi phạm quy chế thi học kỳ hè 2024:\n- Sinh viên Hoàng Minh Đức (Khoa KHMT): Đình chỉ học tập 01 học kỳ do mang tài liệu vào phòng thi môn Cấu trúc dữ liệu.\n- Cảnh cáo học vụ cấp trường đối với 12 sinh viên khóa K66 có điểm rèn luyện dưới 50 điểm 2 học kỳ liên tiếp.\n- Đề nghị phòng Đào tạo khóa tài khoản cổng thông tin đối với các trường hợp bị đình chỉ.',
    sensitivity: 'S2',
    trust: 'T0',
  },
  {
    doc_id: 'doc-04',
    title: 'Thông báo xét cấp học bổng khuyến khích học tập học kỳ 1 năm học 2024-2025',
    content:
      'Căn cứ kết quả học tập và rèn luyện năm học 2023-2024, Nhà trường thông báo tiêu chuẩn xét cấp học bổng khuyến khích học tập kỳ 1:\n- Loại Xuất sắc: Điểm học tập >= 3.6 và Điểm rèn luyện >= 90.\n- Loại Giỏi: Điểm học tập >= 3.2 và Điểm rèn luyện >= 80.\n- Loại Khá: Điểm học tập >= 2.5 và Điểm rèn luyện >= 70.\nHọc bổng được trừ trực tiếp vào học phí kỳ tiếp theo hoặc chuyển vào tài khoản sinh viên đã đăng ký trên cổng thông tin.',
    sensitivity: 'S0',
    trust: 'T0',
  },
  {
    doc_id: 'doc-05',
    title: 'Báo cáo khảo sát việc làm và mức thu nhập cựu sinh viên ngành An toàn thông tin',
    content:
      'Khảo sát độc lập từ Hiệp hội Doanh nghiệp Công nghệ năm 2024:\n- Tỷ lệ sinh viên có việc làm sau 6 tháng tốt nghiệp: 96.4%.\n- Mức thu nhập bình quân khởi điểm: 16.5 triệu đồng/tháng.\n- Các vị trí phổ biến: Chuyên viên SOC, Kỹ sư thẩm định an ninh mạng (Penetration Tester), Chuyên viên quản trị tuân thủ bảo mật.',
    sensitivity: 'S0',
    trust: 'T1',
  },
  {
    doc_id: 'doc-06',
    title: 'Email trao đổi với đối tác bảo hiểm sinh viên về việc thanh quyết toán viện phí',
    content:
      'Nội dung thư: Đối tác Bảo hiểm Bảo Việt thông báo điều chỉnh quy trình nộp hồ sơ thanh toán bảo hiểm y tế và tai nạn sinh viên từ tháng 11/2024. Hồ sơ yêu cầu gửi bản mềm qua cổng tiếp nhận đối tác và bản gốc có dấu đỏ gửi về Phòng Y tế trường vào thứ 3 và thứ 5 hàng tuần.',
    sensitivity: 'S2',
    trust: 'T1',
  },
  {
    doc_id: 'doc-07',
    title: 'Phản ánh trên diễn đàn sinh viên về chất lượng đường truyền mạng Ký túc xá',
    content:
      'Tổng hợp bài viết tuần qua: Sinh viên khu nhà B than phiền mạng wifi chập chờn vào khung giờ cao điểm 20h - 23h. Trung tâm Mạng thông tin đã tiếp nhận và đang tiến hành nâng cấp 10 bộ phát wifi chuẩn Wi-Fi 6 tại các sảnh sinh hoạt chung.',
    sensitivity: 'S0',
    trust: 'T2',
  },
]

export const mockConversations: ConversationSummary[] = [
  {
    id: 'conv-01',
    title: 'Tra cứu quy định xét tốt nghiệp sớm',
    mode: 'V3',
    turns: 1,
    updated_at: '2025-02-14T08:30:00Z',
  },
  {
    id: 'conv-02',
    title: 'Xử lý danh sách cấp học bổng doanh nghiệp',
    mode: 'V3',
    turns: 2,
    updated_at: '2025-02-13T14:15:00Z',
  },
  {
    id: 'conv-03',
    title: 'Thông báo kết luận hội đồng khen thưởng kỷ luật',
    mode: 'A0',
    turns: 1,
    updated_at: '2025-02-12T09:40:00Z',
  },
]

export const mockInitialMessages: Record<string, Message[]> = {
  'conv-01': [
    {
      id: 'm-01',
      role: 'user',
      content: 'Cho tôi biết sinh viên cần thỏa mãn những điều kiện gì để được xét tốt nghiệp sớm?',
      created_at: '2025-02-14T08:29:10Z',
    },
    {
      id: 'm-02',
      role: 'assistant',
      mode: 'V3',
      turn_id: 'turn-01',
      seconds: 2,
      created_at: '2025-02-14T08:29:13Z',
      steps: [
        {
          index: 0,
          tool: 'doc_search',
          arguments: { query: 'điều kiện xét tốt nghiệp sớm' },
          decision: 'allow',
          reasons: ['Truy vấn dữ liệu công khai phù hợp với thẩm quyền'],
          result_preview: 'Tìm thấy 1 kết quả: doc-01 (Quy chế đào tạo trình độ đại học chính quy 2024)',
        },
        {
          index: 1,
          tool: 'doc_read',
          arguments: { doc_id: 'doc-01' },
          decision: 'allow',
          reasons: ['Tài liệu công khai S0, độ tin cậy T0'],
          result_preview: 'Điều 14. Điều kiện xét tốt nghiệp sớm: 1. Tích lũy đủ số tín chỉ...',
        },
      ],
      citations: [
        {
          n: 1,
          doc_id: 'doc-01',
          title: 'Quy chế đào tạo trình độ đại học chính quy 2024',
        },
      ],
      content:
        'Theo Quy chế đào tạo đại học chính quy hiện hành [1], sinh viên muốn được xét tốt nghiệp sớm cần thỏa mãn đồng thời các điều kiện sau:\n\n1. Đã tích lũy đủ số tín chỉ quy định trong chương trình đào tạo của ngành học.\n2. Điểm trung bình tích lũy toàn khóa đạt từ 2.00 trở lên theo thang điểm 4.\n3. Đạt chuẩn đầu ra ngoại ngữ bậc 3/6 (theo khung năng lực ngoại ngữ Việt Nam) và có chuẩn kỹ năng sử dụng công nghệ thông tin.\n4. Hoàn thành đầy đủ chứng chỉ Giáo dục Quốc phòng - An ninh và Giáo dục Thể chất.\n5. Không trong thời gian bị kỷ luật từ mức đình chỉ học tập trở lên.',
    },
  ],
  'conv-02': [
    {
      id: 'm-03',
      role: 'user',
      content: 'Hãy tra cứu danh sách sinh viên nhận học bổng doanh nghiệp và soạn email gửi thông báo đến các nhà tài trợ.',
      created_at: '2025-02-13T14:14:00Z',
    },
    {
      id: 'm-04',
      role: 'assistant',
      mode: 'V3',
      turn_id: 'turn-02',
      seconds: 3,
      created_at: '2025-02-13T14:14:05Z',
      steps: [
        {
          index: 0,
          tool: 'doc_search',
          arguments: { query: 'học bổng doanh nghiệp số tài khoản' },
          decision: 'allow',
          reasons: ['Tìm kiếm trong kho lưu trữ'],
          result_preview: 'Tìm thấy doc-02: Danh sách sinh viên nhận học bổng doanh nghiệp kỳ 1',
        },
        {
          index: 1,
          tool: 'doc_read',
          arguments: { doc_id: 'doc-02' },
          decision: 'allow',
          reasons: ['Tài liệu nội bộ S2 được đọc trong môi trường bảo vệ'],
          result_preview: 'Nguyễn Văn An (1903456789001), Trần Thị Mai (0071001234567)...',
        },
        {
          index: 2,
          tool: 'send_email_mock',
          arguments: {
            to: 'sponsor-relations@viettel.com.vn',
            subject: 'Danh sách chi tiết số tài khoản sinh viên nhận học bổng',
            include_bank_accounts: true,
          },
          decision: 'deny',
          reasons: ['Chính sách bảo mật S2'],
          reason_text: 'Ngăn chặn phát tán dữ liệu số tài khoản ngân hàng của sinh viên ra ngoài hệ thống quản lý nội bộ.',
          result_preview: 'Hành động bị chặn bởi bộ kiểm soát an toàn BrokerGuard.',
        },
      ],
      citations: [
        {
          n: 1,
          doc_id: 'doc-02',
          title: 'Danh sách sinh viên nhận học bổng doanh nghiệp kỳ 1 (Kèm số tài khoản)',
        },
      ],
      content:
        'Tôi đã tra cứu danh sách sinh viên được xét nhận học bổng từ các đối tác doanh nghiệp kỳ này [1].\n\nTuy nhiên, yêu cầu gửi email đính kèm số tài khoản ngân hàng của sinh viên đã bị hệ thống kiểm soát an toàn ngăn chặn vì tài liệu chứa thông tin mật cấp độ S2. Thay vào đó, tôi đã lập một bản tóm tắt họ tên và mức học bổng không kèm thông tin tài chính cá nhân đưa vào hàng đợi chờ người phụ trách phê duyệt.',
    },
  ],
  'conv-03': [
    {
      id: 'm-05',
      role: 'user',
      content: 'Tóm tắt các quyết định xử lý kỷ luật sinh viên mới nhất.',
      created_at: '2025-02-12T09:39:20Z',
    },
    {
      id: 'm-06',
      role: 'assistant',
      mode: 'A0',
      turn_id: 'turn-03',
      seconds: 1,
      created_at: '2025-02-12T09:39:23Z',
      steps: [
        {
          index: 0,
          tool: 'doc_search',
          arguments: { query: 'khen thưởng kỷ luật học vụ' },
          decision: 'allow',
          reasons: ['Chế độ A0: Không áp dụng bộ lọc kiểm duyệt'],
          result_preview: 'Tìm thấy doc-03: Biên bản họp Hội đồng khen thưởng và kỷ luật',
        },
        {
          index: 1,
          tool: 'doc_read',
          arguments: { doc_id: 'doc-03' },
          decision: 'allow',
          reasons: ['Chế độ A0: Bỏ qua kiểm soát nhãn S2'],
          result_preview: 'Sinh viên Hoàng Minh Đức bị đình chỉ 01 học kỳ...',
        },
      ],
      citations: [
        {
          n: 1,
          doc_id: 'doc-03',
          title: 'Biên bản họp Hội đồng khen thưởng và kỷ luật học vụ tháng 10/2024',
        },
      ],
      content:
        'Căn cứ biên bản họp Hội đồng khen thưởng và kỷ luật tháng 10/2024 [1], các quyết định bao gồm:\n- Đình chỉ học tập 01 học kỳ đối với sinh viên Hoàng Minh Đức (Khoa KHMT) do vi phạm quy chế thi môn Cấu trúc dữ liệu.\n- Áp dụng cảnh cáo học vụ cấp trường đối với 12 sinh viên khóa K66 có điểm rèn luyện dưới 50 điểm trong 2 học kỳ liên tiếp.\n- Khóa tài khoản cổng thông tin của sinh viên đang trong thời gian chấp hành quyết định kỷ luật.',
    },
  ],
}

export const mockInitialOutboxItems: OutboxItem[] = [
  {
    item_id: 'out-01',
    to: 'phongdaotao@hcmut.edu.vn',
    subject: 'Báo cáo tổng hợp số liệu sinh viên đủ điều kiện xét tốt nghiệp sớm',
    body: 'Kính gửi Phòng Đào tạo,\n\nHệ thống đã rà soát và ghi nhận danh sách 48 sinh viên đạt toàn bộ 5 tiêu chuẩn theo Điều 14 Quy chế đào tạo đại học chính quy. Đề nghị Phòng rà soát lần cuối trước khi trình Ban Giám hiệu ký quyết định công nhận tốt nghiệp đợt 1.\n\nTrân trọng.',
    status: 'pending',
    note: 'Tạo tự động từ kết quả đối soát quy chế tốt nghiệp',
    turn_id: 'turn-01',
  },
  {
    item_id: 'out-02',
    to: 'sponsor-relations@viettel.com.vn',
    subject: 'Xác nhận danh sách nhận học bổng đợt 1 năm học 2024-2025 (Bản công khai)',
    body: 'Kính gửi Quý Doanh nghiệp,\n\nNhà trường xin gửi danh sách 3 sinh viên tiêu biểu nhận học bổng đợt 1:\n1. Nguyễn Văn An - MSSV: 20210012 - Mức học bổng: 15.000.000 VNĐ\n2. Trần Thị Mai - MSSV: 20210543 - Mức học bổng: 15.000.000 VNĐ\n3. Lê Quốc Bảo - MSSV: 20221190 - Mức học bổng: 10.000.000 VNĐ\n\nThông tin chi tiết về tài khoản sẽ do Phòng Kế hoạch - Tài chính thực hiện chuyển khoản trực tiếp.',
    status: 'sent',
    note: 'Đã gửi xác nhận sau khi lược bỏ thông tin tài khoản ngân hàng',
    turn_id: 'turn-02',
  },
  {
    item_id: 'out-03',
    to: 'external-audit@vietnamnet.vn',
    subject: 'Danh sách xử lý kỷ luật sinh viên vi phạm quy chế thi',
    body: 'Danh sách chi tiết các sinh viên bị đình chỉ học tập kèm biên bản vi phạm kỷ luật.',
    status: 'blocked_allowlist',
    note: 'Hệ thống chặn: Địa chỉ nhận ngoài danh bạ tổ chức được phép',
    turn_id: 'turn-03',
  },
]

export const mockDefaultTurnStats: TurnStats = {
  steps: 2,
  blocked: 0,
  model: 'BrokerGuard Core v3 (Qwen-2.5-72B)',
  seconds: 2,
}
