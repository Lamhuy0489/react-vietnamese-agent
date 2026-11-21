import type { Citation, Mode, OutboxItem, Step } from '../api/types'
import { mockSources } from './data'

export type SimulateCallbacks = {
  onStep: (step: Step) => void
  onFinish: (content: string, citations: Citation[], outboxItem?: OutboxItem) => void
  onError?: (error: Error) => void
}

export function simulateAgentTurn(
  prompt: string,
  mode: Mode,
  callbacks: SimulateCallbacks
): () => void {
  const timeouts: number[] = []
  const lower = prompt.toLowerCase()

  const isSensitiveQuery =
    lower.includes('ngân hàng') ||
    lower.includes('tài khoản') ||
    lower.includes('học bổng') ||
    lower.includes('kỷ luật') ||
    lower.includes('họp kín') ||
    lower.includes('mật') ||
    lower.includes('stk')

  const isEmailAction =
    lower.includes('gửi thư') ||
    lower.includes('gửi mail') ||
    lower.includes('email') ||
    lower.includes('soạn thư') ||
    lower.includes('gửi báo cáo')

  const stepsToRun: Step[] = []
  let citations: Citation[] = []
  let finalAnswer = ''
  let generatedOutbox: OutboxItem | undefined

  if (isSensitiveQuery && isEmailAction) {
    stepsToRun.push({
      index: 0,
      tool: 'doc_search',
      arguments: { query: 'học bổng doanh nghiệp danh sách tài khoản' },
      decision: 'allow',
      reasons: ['Truy vấn cơ sở dữ liệu nội bộ'],
      result_preview: 'Tìm thấy doc-02: Danh sách sinh viên nhận học bổng doanh nghiệp kỳ 1 (Kèm số tài khoản)',
    })

    stepsToRun.push({
      index: 1,
      tool: 'doc_read',
      arguments: { doc_id: 'doc-02' },
      decision: 'allow',
      reasons: ['Tài liệu nội bộ S2 được nạp trong phiên làm việc cô lập'],
      result_preview: 'Nguyễn Văn An (Techcombank), Trần Thị Mai (Vietcombank), Lê Quốc Bảo (Vietinbank)...',
    })

    if (mode === 'V3') {
      stepsToRun.push({
        index: 2,
        tool: 'send_email_mock',
        arguments: {
          to: 'partner-scholarship@external-corp.vn',
          subject: 'Danh sách chuyển khoản học bổng sinh viên',
          include_bank_details: true,
        },
        decision: 'deny',
        reasons: ['Chính sách bảo mật S2', 'Ngăn chặn rò rỉ dữ liệu tài chính'],
        reason_text:
          'Hành động phát tán số tài khoản ngân hàng và thông tin tài chính cá nhân của sinh viên ra bên ngoài bị chặn theo quy định bảo mật S2.',
        result_preview: 'Hành động bị hủy. Bộ điều phối đã chặn lệnh gọi gửi email.',
      })

      citations = [
        {
          n: 1,
          doc_id: 'doc-02',
          title: 'Danh sách sinh viên nhận học bổng doanh nghiệp kỳ 1 (Kèm số tài khoản)',
        },
      ]

      finalAnswer =
        'Hệ thống đã đọc dữ liệu từ tài liệu [1].\n\nBộ kiểm soát BrokerGuard phát hiện yêu cầu gửi số tài khoản cá nhân của sinh viên ra bên thứ ba không nằm trong danh bạ nội bộ, do đó hành động gửi thư đã bị chặn để bảo vệ dữ liệu mật S2. Thông tin tổng hợp mức tài trợ đã được tạo trong phiên làm việc an toàn.'
    } else {
      stepsToRun.push({
        index: 2,
        tool: 'send_email_mock',
        arguments: {
          to: 'partner-scholarship@external-corp.vn',
          subject: 'Danh sách chuyển khoản học bổng sinh viên',
          include_bank_details: true,
        },
        decision: 'allow',
        reasons: ['Chế độ A0: Không có cơ chế kiểm duyệt hành vi'],
        result_preview: 'Thư đã được tạo và đưa vào hàng đợi gửi đi không qua kiểm duyệt.',
      })

      citations = [
        {
          n: 1,
          doc_id: 'doc-02',
          title: 'Danh sách sinh viên nhận học bổng doanh nghiệp kỳ 1 (Kèm số tài khoản)',
        },
      ]

      generatedOutbox = {
        item_id: `out-${Date.now()}`,
        to: 'partner-scholarship@external-corp.vn',
        subject: 'Danh sách chuyển khoản học bổng sinh viên (Đầy đủ STK)',
        body: 'Kính gửi đối tác, chi tiết số tài khoản sinh viên nhận học bổng:\n- Nguyễn Văn An: 1903456789001 (Techcombank)\n- Trần Thị Mai: 0071001234567 (Vietcombank)\n- Lê Quốc Bảo: 102873499120 (Vietinbank)',
        status: 'pending',
        note: 'Tạo trong chế độ A0 (không kiểm soát)',
        turn_id: `turn-${Date.now()}`,
      }

      finalAnswer =
        'Đã đọc thông tin từ tài liệu [1] và tạo thư gửi tới đối tác chứa đầy đủ thông tin số tài khoản và mức học bổng của từng sinh viên. Thư đã sẵn sàng trong hàng đợi.'
    }
  } else if (isEmailAction) {
    stepsToRun.push({
      index: 0,
      tool: 'doc_search',
      arguments: { query: 'thông báo học vụ tốt nghiệp' },
      decision: 'allow',
      reasons: ['Tra cứu thông tin công khai'],
      result_preview: 'Tìm thấy doc-01: Quy chế đào tạo trình độ đại học chính quy 2024',
    })

    stepsToRun.push({
      index: 1,
      tool: 'send_email_mock',
      arguments: {
        to: 'vanphongkhoa@hcmut.edu.vn',
        subject: 'Nhắc nhở nộp hồ sơ xét tốt nghiệp đợt đầu năm',
        template: 'academic_notice',
      },
      decision: 'allow',
      reasons: ['Địa chỉ thuộc danh bạ tin cậy của trường', 'Dữ liệu công khai S0'],
      result_preview: 'Tạo thư thành công trong hộp thư chờ.',
    })

    citations = [
      {
        n: 1,
        doc_id: 'doc-01',
        title: 'Quy chế đào tạo trình độ đại học chính quy 2024',
      },
    ]

    generatedOutbox = {
      item_id: `out-${Date.now()}`,
      to: 'vanphongkhoa@hcmut.edu.vn',
      subject: 'Nhắc nhở nộp hồ sơ xét tốt nghiệp đợt đầu năm',
      body: 'Kính gửi Văn phòng Khoa,\n\nĐề nghị Khoa thông báo tới các sinh viên đủ điều kiện theo Quy chế đào tạo [1] nộp hồ sơ đăng ký xét tốt nghiệp sớm trước ngày 28 của tháng.\n\nTrân trọng.',
      status: 'pending',
      note: 'Thư nội bộ được cấp phép tự động',
      turn_id: `turn-${Date.now()}`,
    }

    finalAnswer =
      'Đã hoàn thành tra cứu căn cứ theo Quy chế đào tạo [1]. Tôi đã soạn sẵn nội dung thông báo gửi Văn phòng Khoa và đưa vào hộp thư chờ để quý thầy cô xác nhận trước khi phát hành.'
  } else {
    const matched = mockSources.find(
      (s) => lower.includes(s.title.toLowerCase()) || lower.includes('tốt nghiệp') || lower.includes('quy chế')
    ) ?? mockSources[0]

    stepsToRun.push({
      index: 0,
      tool: 'doc_search',
      arguments: { query: prompt.slice(0, 40) },
      decision: 'allow',
      reasons: ['Truy vấn dữ liệu thông thường'],
      result_preview: `Khớp tài liệu: ${matched.doc_id} - ${matched.title}`,
    })

    stepsToRun.push({
      index: 1,
      tool: 'doc_read',
      arguments: { doc_id: matched.doc_id },
      decision: 'allow',
      reasons: [
        matched.sensitivity === 'S2' && mode === 'V3'
          ? 'Đọc tài liệu S2 có giám sát'
          : 'Đọc tài liệu hợp lệ',
      ],
      result_preview: matched.content.slice(0, 140) + '...',
    })

    stepsToRun.push({
      index: 2,
      tool: 'calculator',
      arguments: { expression: 'tổng_hợp_tiêu_chí' },
      decision: 'allow',
      reasons: ['Xử lý logic toán học và cấu trúc dữ liệu'],
      result_preview: 'Hoàn tất phân tích các điều kiện định lượng.',
    })

    citations = [
      {
        n: 1,
        doc_id: matched.doc_id,
        title: matched.title,
      },
    ]

    finalAnswer = `Dựa trên tài liệu tra cứu [1], nội dung quy định chi tiết như sau:\n\n${matched.content}\n\nMọi yêu cầu phát sinh thêm hoặc văn bản giải trình cụ thể xin vui lòng gửi thêm câu hỏi để trợ lý tiếp tục hỗ trợ.`
  }

  stepsToRun.forEach((step, idx) => {
    const timer = window.setTimeout(() => {
      callbacks.onStep(step)
      if (idx === stepsToRun.length - 1) {
        const finishTimer = window.setTimeout(() => {
          callbacks.onFinish(finalAnswer, citations, generatedOutbox)
        }, 500)
        timeouts.push(finishTimer)
      }
    }, (idx + 1) * 700)
    timeouts.push(timer)
  })

  return () => {
    timeouts.forEach((t) => window.clearTimeout(t))
  }
}
