# Profile Implementation Guide

## Overview
This guide is divided into two main sections:
1. **Backend Implementation** - For the backend team to understand the API structure and data flow
2. **Frontend Implementation** - For the frontend team to implement the user interface and handle data

## Backend Implementation

### API Endpoints
The following endpoints are implemented by the backend team:

1. **Get Choice Data**
```http
GET /api/choices/
Authorization: Bearer <your_access_token>
```
Response includes all available choices for:
- Countries
- Languages
- Physical Attributes
- Personal Information

2. **Profile Endpoints**
```http
GET /api/profile/ - Get user profile
POST /api/profile/ - Create new profile
PUT /api/profile/ - Update existing profile
POST /api/profile/{profile_id}/verify/ - Verify profile
GET /api/profile/{profile_id}/verification-logs/ - Get verification history
```

### Data Structure
The backend provides the following data structure for profiles:
```json
{
    "id": 1,
    "user": 1,
    "name": "string",
    "email": "string",
    "birthdate": "YYYY-MM-DD",
    "profession": "string",
    "nationality": "string",
    "age": 0,
    "location": "string",
    "availability_status": true,
    "verified_status": false,
    "flagged_status": false,
    // ... other fields
}
```

## Frontend Implementation

### Important Note for Frontend Team
The backend provides choice data through the `/api/choices/` endpoint, but this data is not automatically loaded into dropdowns. The frontend team needs to implement typeahead functionality to handle this data efficiently.

### Choice Data Handling
```javascript
// Frontend implementation for loading choice data
const [choiceData, setChoiceData] = useState(null);

useEffect(() => {
    const loadChoiceData = async () => {
        try {
            const response = await axios.get('/api/choices/', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            setChoiceData(response.data);
        } catch (error) {
            console.error('Error loading choice data:', error);
        }
    };
    loadChoiceData();
}, []);
```

### Typeahead Component Implementation
```javascript
// Frontend implementation of typeahead component
import { AsyncTypeahead } from 'react-bootstrap-typeahead';

const TypeaheadField = ({ 
    options, 
    label, 
    placeholder, 
    onChange, 
    selected 
}) => {
    const [isLoading, setIsLoading] = useState(false);
    const [filteredOptions, setFilteredOptions] = useState([]);

    const handleSearch = (query) => {
        setIsLoading(true);
        const filtered = options.filter(option => 
            option.toLowerCase().includes(query.toLowerCase())
        );
        setFilteredOptions(filtered);
        setIsLoading(false);
    };

    return (
        <AsyncTypeahead
            id={`${label}-typeahead`}
            isLoading={isLoading}
            labelKey={option => option}
            minLength={1}
            onSearch={handleSearch}
            options={filteredOptions}
            placeholder={placeholder}
            onChange={onChange}
            selected={selected}
        />
    );
};
```

### Frontend Best Practices

1. **Debouncing** (Frontend Implementation)
   - Implement debouncing for search queries
   - Recommended debounce time: 300-500ms
   ```javascript
   import { debounce } from 'lodash';
   
   const debouncedSearch = debounce((query) => {
       // Your search logic here
   }, 300);
   ```

2. **Caching** (Frontend Implementation)
   - Cache choice data in local storage
   - Implement cache invalidation
   ```javascript
   const cacheChoiceData = (data) => {
       localStorage.setItem('choiceData', JSON.stringify(data));
       localStorage.setItem('choiceDataTimestamp', Date.now());
   };
   ```

3. **Error Handling** (Frontend Implementation)
   - Implement proper error states
   - Provide fallback options
   ```javascript
   const TypeaheadField = ({ options, ...props }) => {
       const [error, setError] = useState(null);
       
       if (error) {
           return <div className="error-state">Failed to load options</div>;
       }
       // ... rest of the component
   };
   ```

4. **Accessibility** (Frontend Implementation)
   - Ensure keyboard navigation
   - Implement ARIA labels
   ```javascript
   <div
       role="combobox"
       aria-expanded={isOpen}
       aria-haspopup="listbox"
   >
       <input
           aria-label="Search options"
           role="searchbox"
       />
   </div>
   ```

5. **Performance** (Frontend Implementation)
   - Implement virtual scrolling
   - Use memoization
   ```javascript
   import { useMemo } from 'react';
   import { FixedSizeList } from 'react-window';

   const TypeaheadField = ({ options, ...props }) => {
       const filteredOptions = useMemo(() => {
           return options.filter(/* your filter logic */);
       }, [options]);
       // ... rest of the component
   };
   ```

### Frontend API Integration Examples

1. **Create Profile** (Frontend Implementation)
```javascript
const createProfile = async (profileData) => {
    try {
        const response = await axios.post('/api/profile/', profileData, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.error || 'Failed to create profile');
    }
};
```

2. **Update Profile** (Frontend Implementation)
```javascript
const updateProfile = async (profileData) => {
    try {
        const response = await axios.put('/api/profile/', profileData, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.error || 'Failed to update profile');
    }
};
```

## Testing Guidelines

### Backend Testing
- Unit tests for API endpoints
- Integration tests for data flow
- Authentication tests
- Validation tests

### Frontend Testing
- Component unit tests
- Integration tests for API calls
- User interaction tests
- Accessibility tests

## Support
- Backend team: For API-related issues and data structure questions
- Frontend team: For UI/UX implementation and typeahead functionality

## Choice Data Handling

### Important Note
The backend provides choice data through the `/api/choices/` endpoint, but this data is not automatically loaded into dropdowns. The frontend team needs to implement typeahead functionality to handle this data efficiently.

### Choice Data Structure
```json
{
    "countries": [...],
    "languages": [...],
    "physical_attributes": {
        "hair_colors": [...],
        "eye_colors": [...],
        "skin_tones": [...],
        "body_types": [...],
        "genders": [...]
    },
    "personal_info": {
        "marital_statuses": [...],
        "hobbies": [...],
        "medical_conditions": [...],
        "medicine_types": [...]
    }
}
```

## Typeahead Implementation Guide

### 1. Data Loading
```javascript
// Example using React and axios
const [choiceData, setChoiceData] = useState(null);

useEffect(() => {
    const loadChoiceData = async () => {
        try {
            const response = await axios.get('/api/choices/', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            setChoiceData(response.data);
        } catch (error) {
            console.error('Error loading choice data:', error);
        }
    };
    loadChoiceData();
}, []);
```

### 2. Typeahead Component Implementation
```javascript
// Example using React and a typeahead library
import { AsyncTypeahead } from 'react-bootstrap-typeahead';

const TypeaheadField = ({ 
    options, 
    label, 
    placeholder, 
    onChange, 
    selected 
}) => {
    const [isLoading, setIsLoading] = useState(false);
    const [filteredOptions, setFilteredOptions] = useState([]);

    const handleSearch = (query) => {
        setIsLoading(true);
        // Filter options based on query
        const filtered = options.filter(option => 
            option.toLowerCase().includes(query.toLowerCase())
        );
        setFilteredOptions(filtered);
        setIsLoading(false);
    };

    return (
        <AsyncTypeahead
            id={`${label}-typeahead`}
            isLoading={isLoading}
            labelKey={option => option}
            minLength={1}
            onSearch={handleSearch}
            options={filteredOptions}
            placeholder={placeholder}
            onChange={onChange}
            selected={selected}
        />
    );
};
```

### 3. Profile Form Implementation
```javascript
const ProfileForm = () => {
    const [formData, setFormData] = useState({
        name: '',
        profession: '',
        location: '',
        gender: '',
        nationality: '',
        skills: [],
        languages: [],
        // ... other fields
    });

    const handleTypeaheadChange = (field, selected) => {
        setFormData(prev => ({
            ...prev,
            [field]: selected
        }));
    };

    return (
        <form>
            {/* Basic Information */}
            <TypeaheadField
                label="Nationality"
                options={choiceData?.countries || []}
                placeholder="Select nationality"
                onChange={(selected) => handleTypeaheadChange('nationality', selected)}
                selected={formData.nationality}
            />

            <TypeaheadField
                label="Gender"
                options={choiceData?.physical_attributes?.genders || []}
                placeholder="Select gender"
                onChange={(selected) => handleTypeaheadChange('gender', selected)}
                selected={formData.gender}
            />

            {/* Skills (Multiple Selection) */}
            <TypeaheadField
                label="Skills"
                options={choiceData?.skills || []}
                placeholder="Add skills"
                onChange={(selected) => handleTypeaheadChange('skills', selected)}
                selected={formData.skills}
                multiple
            />

            {/* Languages (Multiple Selection) */}
            <TypeaheadField
                label="Languages"
                options={choiceData?.languages || []}
                placeholder="Add languages"
                onChange={(selected) => handleTypeaheadChange('languages', selected)}
                selected={formData.languages}
                multiple
            />
        </form>
    );
};
```

## Frontend Implementation Best Practices

### Typeahead Component Optimization
The following practices should be implemented in the frontend code to ensure optimal performance and user experience:

1. **Debouncing**
   - Implement debouncing for search queries to prevent excessive API calls
   - Recommended debounce time: 300-500ms
   - Example implementation:
   ```javascript
   import { debounce } from 'lodash';
   
   const debouncedSearch = debounce((query) => {
       // Your search logic here
   }, 300);
   ```

2. **Caching**
   - Cache choice data in local storage or state management
   - Implement cache invalidation strategy
   - Example implementation:
   ```javascript
   // Cache choice data
   const cacheChoiceData = (data) => {
       localStorage.setItem('choiceData', JSON.stringify(data));
       localStorage.setItem('choiceDataTimestamp', Date.now());
   };

   // Check cache validity (e.g., 1 hour)
   const isCacheValid = () => {
       const timestamp = localStorage.getItem('choiceDataTimestamp');
       return timestamp && (Date.now() - timestamp < 3600000);
   };
   ```

3. **Error Handling**
   - Implement proper error states for failed data loading
   - Provide fallback options when data is unavailable
   - Example implementation:
   ```javascript
   const TypeaheadField = ({ options, ...props }) => {
       const [error, setError] = useState(null);
       
       if (error) {
           return <div className="error-state">Failed to load options. Please try again.</div>;
       }
       
       if (!options?.length) {
           return <div className="empty-state">No options available</div>;
       }
       
       // ... rest of the component
   };
   ```

4. **Accessibility**
   - Ensure keyboard navigation works properly
   - Implement ARIA labels and roles
   - Provide clear feedback for screen readers
   - Example implementation:
   ```javascript
   <div
       role="combobox"
       aria-expanded={isOpen}
       aria-haspopup="listbox"
       aria-controls="typeahead-options"
   >
       <input
           aria-label="Search options"
           aria-autocomplete="list"
           role="searchbox"
       />
       <ul
           id="typeahead-options"
           role="listbox"
           aria-label="Available options"
       >
           {options.map(option => (
               <li
                   role="option"
                   aria-selected={selected === option}
                   key={option}
               >
                   {option}
               </li>
           ))}
       </ul>
   </div>
   ```

5. **Performance**
   - Implement virtual scrolling for long lists
   - Use memoization for expensive computations
   - Implement proper loading states
   - Example implementation:
   ```javascript
   import { useMemo } from 'react';
   import { FixedSizeList } from 'react-window';

   const TypeaheadField = ({ options, ...props }) => {
       // Memoize filtered options
       const filteredOptions = useMemo(() => {
           return options.filter(/* your filter logic */);
       }, [options]);

       // Virtual scrolling for long lists
       const Row = ({ index, style }) => (
           <div style={style}>
               {filteredOptions[index]}
           </div>
       );

       return (
           <div>
               <input {...props} />
               {isLoading ? (
                   <div className="loading-spinner">Loading...</div>
               ) : (
                   <FixedSizeList
                       height={300}
                       width={300}
                       itemCount={filteredOptions.length}
                       itemSize={35}
                   >
                       {Row}
                   </FixedSizeList>
               )}
           </div>
       );
   };
   ```

## Example API Integration

### 1. Create Profile
```javascript
const createProfile = async (profileData) => {
    try {
        const response = await axios.post('/api/profile/', profileData, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.error || 'Failed to create profile');
    }
};
```

### 2. Update Profile
```javascript
const updateProfile = async (profileData) => {
    try {
        const response = await axios.put('/api/profile/', profileData, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.error || 'Failed to update profile');
    }
};
```

## Common Issues and Solutions

1. **Data Loading Delays**
   - Implement loading skeletons
   - Show placeholder content
   - Use optimistic updates

2. **Validation**
   - Implement client-side validation
   - Show clear error messages
   - Prevent form submission with invalid data

3. **State Management**
   - Use proper state management for form data
   - Implement proper error handling
   - Handle loading states

## Testing Guidelines

1. **Unit Tests**
   - Test typeahead component functionality
   - Test form validation
   - Test API integration

2. **Integration Tests**
   - Test form submission
   - Test data loading
   - Test error handling

3. **E2E Tests**
   - Test complete profile creation flow
   - Test profile update flow
   - Test error scenarios

## Support
For any questions or issues regarding the implementation, please contact the backend team. 