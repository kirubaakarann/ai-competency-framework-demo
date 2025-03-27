from flask import Flask, render_template, jsonify
import os
from competency_framework import CompetencyFramework
import json

app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize the framework
framework = CompetencyFramework("static/competency_data.json")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user/<user_id>')
def get_user_data(user_id):
    # Generate visualization data on-the-fly
    user = framework.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"User {user_id} not found"}), 404
        
    # Get role information
    role = framework.get_role_by_title(user['current_role'])
    
    # Get gap analysis
    gaps = framework.analyze_gaps(user_id)
    
    # Get career paths
    career_paths = framework.identify_career_paths(user_id)
    
    # Build the visualization data structure
    viz_data = {
        "user": {
            "id": user['id'],
            "name": user['name'],
            "role": user['current_role']
        },
        "competencies": [],
        "careerPaths": []
    }
    
    # Add competency data (current vs. required)
    for comp_id, required_level in role['required_competencies'].items():
        current_level = user['assessed_competencies'].get(comp_id, 0)
        comp_name = framework.competency_map[comp_id]['name'] if comp_id in framework.competency_map else comp_id
        
        # Determine if this is a gap or strength
        is_gap = current_level < required_level
        
        viz_data["competencies"].append({
            "id": comp_id,
            "name": comp_name,
            "currentLevel": current_level,
            "requiredLevel": required_level,
            "isGap": is_gap
        })
    
    # Add career path data
    for path in career_paths['career_paths']:
        path_data = {
            "role": path['role'],
            "feasibilityScore": path['feasibility_score'],
            "developmentAreas": path['development_areas'],
            "gaps": []
        }
        
        # Add specific gaps for this career path
        for comp_id, gap in path['competency_gaps'].items():
            path_data["gaps"].append({
                "id": comp_id,
                "name": gap['competency_name'],
                "currentLevel": gap['current_level'],
                "requiredLevel": gap['required_level'],
                "gap": gap['gap']
            })
        
        viz_data["careerPaths"].append(path_data)
    
    return jsonify(viz_data)

if __name__ == '__main__':
    # Use environment variable for port if available (Render will set this)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
