"""
Create dummy podcast files for local testing of the feedback system.
"""

import wave
import struct
import math
from pathlib import Path

def create_dummy_wav(filename, duration_seconds=30, sample_rate=22050):
    """Create a dummy WAV file with a simple tone."""
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = []
        for i in range(int(sample_rate * duration_seconds)):
            t = float(i) / sample_rate
            # Create a simple tone with some variation
            frequency = 220 + 50 * math.sin(t * 0.3)  # Varying frequency
            amplitude = 8000 * (0.5 + 0.3 * math.sin(t * 2))  # Varying amplitude
            wave_value = int(amplitude * math.sin(frequency * 2 * math.pi * t))
            frames.append(struct.pack('<h', wave_value))
        
        wav_file.writeframes(b''.join(frames))

def create_dummy_podcasts():
    """Create several dummy podcast files for testing."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    podcasts = [
        {
            "filename": "Azure_Fundamentals_Introduction",
            "duration": 45,
            "script": """Sarah: Welcome to today's episode about Azure Fundamentals!

Mike: Thanks Sarah! I'm really excited to dive into the basics of Microsoft Azure cloud computing.

Sarah: Perfect! Let's start with what Azure actually is. Azure is Microsoft's comprehensive cloud computing platform that provides a wide range of services.

Mike: That's right! It includes everything from virtual machines and storage to AI services and databases. What makes it special compared to traditional on-premises infrastructure?

Sarah: Great question! The main advantages are scalability, cost-effectiveness, and global reach. You only pay for what you use, and you can scale resources up or down based on demand.

Mike: And the security features are enterprise-grade, which is crucial for businesses moving to the cloud.

Sarah: Absolutely! Azure also offers excellent integration with existing Microsoft technologies, making migration smoother for many organizations.

Mike: Thanks for this introduction to Azure Fundamentals! This gives our listeners a solid foundation to build upon.

Sarah: My pleasure! In our next episode, we'll dive deeper into Azure compute services. Thanks for listening!"""
        },
        {
            "filename": "Azure_Storage_Solutions_Deep_Dive",
            "duration": 38,
            "script": """Sarah: Today we're exploring Azure Storage solutions - one of the most fundamental services in the Azure ecosystem.

Mike: Storage is definitely critical! Sarah, can you walk us through the different types of storage Azure offers?

Sarah: Of course! Azure provides four main storage services: Blob storage for unstructured data, File storage for shared file systems, Queue storage for messaging, and Table storage for NoSQL data.

Mike: Blob storage is probably what most people encounter first, right? It's great for storing documents, images, and videos.

Sarah: Exactly! And it offers different access tiers - Hot for frequently accessed data, Cool for infrequently accessed data, and Archive for rarely accessed data. This helps optimize costs significantly.

Mike: The pricing model is really clever. You pay less for storage that you access less frequently, but retrieval costs are higher for cooler tiers.

Sarah: That's the key insight! It's all about matching your storage tier to your access patterns. Most applications can save substantial money by using the right combination of tiers.

Mike: What about security and compliance? That's always a concern with cloud storage.

Sarah: Azure Storage provides encryption at rest and in transit, plus integration with Azure Active Directory for access control. It also meets major compliance standards like GDPR and HIPAA.

Mike: Excellent overview of Azure Storage! This will help our listeners choose the right storage solutions for their needs.

Sarah: Thanks Mike! Next time we'll cover Azure networking fundamentals."""
        },
        {
            "filename": "Understanding_Azure_Active_Directory",
            "duration": 42,
            "script": """Mike: Welcome back! Today Sarah and I are discussing Azure Active Directory - the identity and access management service that's central to Azure security.

Sarah: Thanks Mike! Azure AD is really the foundation of identity management in the cloud. It's much more than just a directory service.

Mike: That's a great point. For listeners who might be familiar with on-premises Active Directory, how does Azure AD differ?

Sarah: While they share some concepts, Azure AD is built for the cloud-first world. It handles authentication and authorization for cloud applications, supports modern protocols like OAuth and SAML, and provides advanced security features.

Mike: The single sign-on capabilities are incredible. Users can access hundreds of applications with one set of credentials.

Sarah: Exactly! And from a security perspective, Azure AD provides multi-factor authentication, conditional access policies, and identity protection features that use machine learning to detect suspicious activities.

Mike: Conditional access is particularly powerful. You can create policies that adapt access requirements based on user location, device compliance, and risk level.

Sarah: Right! For example, you might require MFA only when users access sensitive applications or sign in from unfamiliar locations. It balances security with user experience.

Mike: What about integration with third-party applications? Not everything is Microsoft.

Sarah: Azure AD supports thousands of pre-integrated SaaS applications, and you can also connect custom applications using standard protocols. It's designed to be the identity hub for your entire ecosystem.

Mike: The reporting and analytics capabilities also provide great insights into user behavior and potential security issues.

Sarah: Absolutely! Azure AD is essential for any organization moving to the cloud. It provides the security and compliance foundation that modern businesses need.

Mike: Thanks for that comprehensive overview of Azure AD, Sarah! Next episode, we'll explore Azure networking concepts."""
        },
        {
            "filename": "Azure_Networking_Essentials_Guide",
            "duration": 35,
            "script": """Sarah: Today we're diving into Azure networking - the backbone that connects all your Azure resources securely and efficiently.

Mike: Networking can seem complex, but it's really about connecting resources and controlling traffic flow. Sarah, what are the core networking concepts in Azure?

Sarah: The foundation is the Virtual Network, or VNet. Think of it as your private network in the Azure cloud where you can deploy resources like virtual machines, databases, and applications.

Mike: And subnets let you segment that VNet into smaller, more manageable pieces, right?

Sarah: Exactly! Subnets help with organization and security. You might put web servers in one subnet and databases in another, then use Network Security Groups to control traffic between them.

Mike: Network Security Groups are like firewalls that operate at the subnet and network interface level. They use rules to allow or deny traffic based on source, destination, port, and protocol.

Sarah: That's right! And for connecting to on-premises networks, Azure provides VPN Gateway for encrypted connections over the internet, and ExpressRoute for dedicated private connections.

Mike: ExpressRoute is great for enterprises that need predictable bandwidth and lower latency to Azure.

Sarah: For global applications, Azure also provides load balancers and traffic managers to distribute traffic across multiple regions and ensure high availability.

Mike: The Application Gateway is particularly useful for web applications - it provides SSL termination, URL-based routing, and Web Application Firewall capabilities.

Sarah: All of these services work together to create secure, scalable, and performant network architectures in Azure.

Mike: Thanks Sarah! This gives our listeners a solid foundation for planning their Azure network infrastructure.

Sarah: You're welcome! Next time we'll explore Azure compute services in detail."""
        },
        {
            "filename": "Azure_Security_Best_Practices_Overview",
            "duration": 40,
            "script": """Mike: Security is paramount in cloud computing, so today Sarah and I are discussing Azure security best practices that every organization should implement.

Sarah: Absolutely Mike! Security in Azure follows a shared responsibility model - Microsoft secures the underlying platform, but customers are responsible for securing their data and applications.

Mike: That's a crucial distinction. What are the foundational security principles organizations should follow?

Sarah: First is the principle of least privilege - give users and applications only the minimum access they need. Azure Role-Based Access Control makes this manageable at scale.

Mike: And defense in depth is equally important - using multiple layers of security controls rather than relying on a single solution.

Sarah: Exactly! This might include network security groups, application firewalls, encryption, and monitoring tools working together.

Mike: Speaking of encryption, Azure provides encryption at rest and in transit by default for most services, but organizations should verify their specific requirements are met.

Sarah: Key management is critical too. Azure Key Vault provides centralized, secure storage for keys, secrets, and certificates, with hardware security module backing available.

Mike: Monitoring and logging are often overlooked but essential. Azure Security Center and Azure Sentinel provide comprehensive security monitoring and threat detection.

Sarah: Security Center gives you a unified view of security posture across your Azure resources and provides actionable recommendations for improvement.

Mike: And don't forget about identity protection! We covered Azure AD earlier, but enabling features like multi-factor authentication and conditional access policies is crucial.

Sarah: Regular security assessments and staying updated with Azure security features are also important. Microsoft continuously adds new security capabilities.

Mike: The security landscape is always evolving, so continuous learning and adaptation are key.

Sarah: Great summary Mike! Security should be built into every aspect of your Azure architecture from day one.

Mike: Thanks Sarah! Our listeners now have a solid foundation for implementing security best practices in Azure."""
        }
    ]
    
    for podcast in podcasts:
        # Create the WAV file
        wav_filename = f"{podcast['filename']}.wav"
        wav_path = output_dir / wav_filename
        create_dummy_wav(str(wav_path), podcast['duration'])
        
        # Create the script file
        script_filename = f"{podcast['filename']}_script.txt"
        script_path = output_dir / script_filename
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(podcast['script'])
        
        print(f"Created: {wav_filename} ({podcast['duration']}s) with script")

if __name__ == "__main__":
    create_dummy_podcasts()
    print("\n✅ All dummy podcasts created successfully!")
    print("You can now test the feedback system at http://localhost:5000/library")