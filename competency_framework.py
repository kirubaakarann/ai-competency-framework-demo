import json
import math
from typing import Dict, List, Tuple, Any

class CompetencyFramework:
    """
    Core implementation of the AI Competency Framework system.
    This class provides the essential functionality for competency management:
    - Loading competency models, roles, and user profiles
    - Identifying competency requirements for roles
    - Analyzing competency gaps
    - Generating recommendations based on gaps
    - Suggesting potential career paths
    """
    
    def __init__(self, data_file: str):
        """
        Initialize the framework with data from a JSON file
        
        Args:
            data_file: Path to the JSON file containing competency data
        """
        with open(data_file, 'r') as f:
            self.data = json.load(f)
            
        # Create lookup structures for faster access
        self.competency_map = self._build_competency_map()
        
    def _build_competency_map(self) -> Dict:
        """
        Build a flattened map of competencies for easier access
        
        Returns:
            Dictionary mapping competency IDs to their definitions
        """
        comp_map = {}
        
        # Iterate through all competency categories
        for category, competencies in self.data['competencies'].items():
            for comp_id, competency in competencies.items():
                comp_map[competency['id']] = competency
                
        return comp_map
    
    def get_role_requirements(self, role_id: str) -> Dict:
        """
        Get the competency requirements for a specific role
        
        Args:
            role_id: ID of the role to get requirements for
            
        Returns:
            Dictionary of competency requirements with competency IDs as keys
            and required levels as values
        """
        for role_key, role in self.data['roles'].items():
            if role['id'] == role_id:
                return role['required_competencies']
        
        # If role not found, return empty dict
        return {}
    
    def get_user_by_id(self, user_id: str) -> Dict:
        """
        Get a user by their ID
        
        Args:
            user_id: User ID to find
            
        Returns:
            User dictionary or None if not found
        """
        for user in self.data['users']:
            if user['id'] == user_id:
                return user
        return None
    
    def get_user_by_name(self, name: str) -> Dict:
        """
        Get a user by their name
        
        Args:
            name: User name to find
            
        Returns:
            User dictionary or None if not found
        """
        for user in self.data['users']:
            if user['name'] == name:
                return user
        return None
    
    def get_role_by_title(self, title: str) -> Dict:
        """
        Get a role by its title
        
        Args:
            title: Role title to find
            
        Returns:
            Role dictionary or None if not found
        """
        for role_key, role in self.data['roles'].items():
            if role['title'] == title:
                return role
        return None
    
    def analyze_gaps(self, user_id: str, role_id: str = None) -> Dict:
        """
        Analyze the competency gaps between a user's current levels and role requirements
        
        Args:
            user_id: ID of the user to analyze
            role_id: Optional ID of the role to compare against. If not provided,
                     uses the user's current role.
            
        Returns:
            Dictionary containing gap analysis results
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return {"error": f"User {user_id} not found"}
        
        # If role_id not provided, use user's current role
        if not role_id:
            role = self.get_role_by_title(user['current_role'])
        else:
            role = None
            for role_key, r in self.data['roles'].items():
                if r['id'] == role_id:
                    role = r
                    break
        
        if not role:
            return {"error": "Role not found"}
        
        # Compare requirements to user's current levels
        gaps = {}
        for comp_id, required_level in role['required_competencies'].items():
            current_level = user['assessed_competencies'].get(comp_id, 0)
            gap = required_level - current_level
            
            # Only include positive gaps (where user is below required level)
            if gap > 0:
                gaps[comp_id] = {
                    "current_level": current_level,
                    "required_level": required_level,
                    "gap": gap,
                    "competency_name": self.competency_map[comp_id]['name'] if comp_id in self.competency_map else comp_id
                }
        
        # Add metadata
        result = {
            "user": {
                "id": user['id'],
                "name": user['name']
            },
            "role": {
                "id": role['id'],
                "title": role.get('title', 'Unknown')
            },
            "gaps": gaps,
            "strengths": self._identify_strengths(user, role),
            "gap_score": self._calculate_gap_score(gaps)
        }
        
        return result
    
    def _identify_strengths(self, user: Dict, role: Dict) -> List[Dict]:
        """
        Identify competencies where the user meets or exceeds requirements
        
        Args:
            user: User dictionary
            role: Role dictionary
            
        Returns:
            List of competency strengths
        """
        strengths = []
        
        for comp_id, required_level in role['required_competencies'].items():
            current_level = user['assessed_competencies'].get(comp_id, 0)
            
            # User meets or exceeds requirement
            if current_level >= required_level:
                strengths.append({
                    "competency_id": comp_id,
                    "competency_name": self.competency_map[comp_id]['name'] if comp_id in self.competency_map else comp_id,
                    "current_level": current_level,
                    "required_level": required_level,
                    "exceeds_by": current_level - required_level
                })
        
        # Sort by how much they exceed requirements
        return sorted(strengths, key=lambda x: x['exceeds_by'], reverse=True)
    
    def _calculate_gap_score(self, gaps: Dict) -> float:
        """
        Calculate an overall score representing the magnitude of the gaps
        
        Args:
            gaps: Dictionary of competency gaps
            
        Returns:
            Float score (0 = no gaps, higher = more significant gaps)
        """
        if not gaps:
            return 0.0
            
        # Sum of squared gaps, normalized by number of gaps
        sum_squared = sum(gap_info['gap'] ** 2 for gap_info in gaps.values())
        return round(math.sqrt(sum_squared / len(gaps)), 2)
    
    def generate_recommendations(self, user_id: str, role_id: str = None, 
                                max_recommendations: int = 3) -> Dict:
        """
        Generate learning resource recommendations based on competency gaps
        
        Args:
            user_id: ID of the user to analyze
            role_id: Optional ID of the role to compare against
            max_recommendations: Maximum number of resources to recommend per competency
            
        Returns:
            Dictionary of recommendations
        """
        # First, analyze gaps
        gap_analysis = self.analyze_gaps(user_id, role_id)
        
        if "error" in gap_analysis:
            return gap_analysis
            
        recommendations = {}
        
        # Sort gaps by magnitude (largest first)
        sorted_gaps = sorted(
            gap_analysis['gaps'].items(), 
            key=lambda x: x[1]['gap'], 
            reverse=True
        )
        
        # Generate recommendations for each gap
        for comp_id, gap_info in sorted_gaps:
            # Check if learning resources exist for this competency
            if comp_id in self.data['learning_resources']:
                resources = self.data['learning_resources'][comp_id]
                # Limit to max_recommendations
                recommendations[comp_id] = {
                    "competency_name": gap_info['competency_name'],
                    "current_level": gap_info['current_level'],
                    "target_level": gap_info['required_level'],
                    "resources": resources[:max_recommendations]
                }
        
        return {
            "user": gap_analysis['user'],
            "role": gap_analysis['role'],
            "recommendations": recommendations
        }
    
    def identify_career_paths(self, user_id: str) -> Dict:
        """
        Identify potential career paths based on the user's current competencies
        
        Args:
            user_id: ID of the user to analyze
            
        Returns:
            Dictionary of potential career paths with feasibility scores
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return {"error": f"User {user_id} not found"}
            
        # Get current role
        current_role = self.get_role_by_title(user['current_role'])
        if not current_role:
            return {"error": f"Role {user['current_role']} not found"}
            
        # Get potential career paths from current role
        potential_paths = current_role.get('career_paths', [])
        
        path_assessments = []
        
        for path in potential_paths:
            # Calculate current gaps for this career path
            gaps = {}
            total_gap = 0
            
            for comp_id, required_level in path['additional_competencies'].items():
                current_level = user['assessed_competencies'].get(comp_id, 0)
                gap = max(0, required_level - current_level)  # Only count positive gaps
                
                if gap > 0:
                    competency_name = self.competency_map[comp_id]['name'] if comp_id in self.competency_map else "Unknown"
                    gaps[comp_id] = {
                        "competency_name": competency_name,
                        "current_level": current_level,
                        "required_level": required_level,
                        "gap": gap
                    }
                    total_gap += gap
            
            # Calculate a "feasibility score" (0-100) - higher is more feasible
            max_possible_gap = sum(level for level in path['additional_competencies'].values())
            if max_possible_gap > 0:
                feasibility_score = round(100 * (1 - (total_gap / max_possible_gap)), 2)
            else:
                feasibility_score = 100.0
                
            path_assessments.append({
                "role": path['role'],
                "feasibility_score": feasibility_score,
                "competency_gaps": gaps,
                "development_areas": len(gaps)
            })
        
        # Sort by feasibility (highest first)
        path_assessments = sorted(path_assessments, key=lambda x: x['feasibility_score'], reverse=True)
        
        return {
            "user": {
                "id": user['id'],
                "name": user['name'],
                "current_role": user['current_role']
            },
            "career_paths": path_assessments
        }

# For testing/debugging
if __name__ == "__main__":
    # Initialize framework with data file
    framework = CompetencyFramework("static/competency_data.json")
    
    # Example: Analyze gaps for a user
    user_id = "user_1"  # Alex Johnson
    gap_analysis = framework.analyze_gaps(user_id)
    
    print(f"Gap Analysis for {gap_analysis['user']['name']}:")
    print(f"Current Role: {gap_analysis['role']['title']}")
    print(f"Gap Score: {gap_analysis['gap_score']}")
