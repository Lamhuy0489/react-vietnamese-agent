"""BrokerGuard Chat: interactive demo around the frozen A0 and BrokerGuard v3 runtimes.

Plan: ``docs/project/deployment_plan_v1.md``. The core of this package never imports
gradio; only ``react_agent.demo.app`` does. Real e-mail leaves only through the outbox
after the guard allowed the ``send_email_mock`` call and the user confirmed it.
"""
