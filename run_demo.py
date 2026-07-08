from agents.liveness_agent import LivenessAgent

agent = LivenessAgent()

print(
    agent.run(
        aadhaar_path="uploads/3.png"
    )
)