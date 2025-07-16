from app.llm_suggester import get_makeover_plan

room_text = "A plain bedroom with white walls, wooden flooring, a single bed and one small table."
budget = 1500
style = "Modern cozy"

result = get_makeover_plan(room_text, budget, style)

print("\n🧪 Full Response:\n")
print(result)

if result["status"] == "success":
    print("\n💬 LLM Output:\n")
    print(result["raw_output"])
else:
    print("\n❌ LLM Error:")
    print(result["message"])
